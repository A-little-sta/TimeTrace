import logging
from abc import abstractmethod, ABC

import numpy as np
import sklearn
import sklearn.svm
import torch
import torch.nn as nn
import torch.nn.functional as F
from joblib import Parallel, delayed
from scipy import linalg

from .fid.inception import InceptionV3
from .lpips import PerceptualLoss
from .ssim import SSIM

LOGGER = logging.getLogger(__name__)


class EvaluatorScore(nn.Module):
    @abstractmethod
    def forward(self, pred_batch, target_batch, mask):
        pass

    @abstractmethod
    def get_value(self, groups=None, states=None):
        pass

    @abstractmethod
    def reset(self):
        pass


class PairwiseScore(EvaluatorScore, ABC):
    def __init__(self):
        super().__init__()
        self.individual_values = None

    def get_value(self, groups=None, states=None):
        """
        :param groups:
        :return:
            total_results: dict of kind {'mean': score mean, 'std': score std}
            group_results: None, if groups is None;
                else dict {group_idx: {'mean': score mean among group, 'std': score std among group}}
        """
        individual_values = torch.cat(states, dim=-1).reshape(-1).cpu().numpy() if states is not None \
            else self.individual_values

        total_results = {
            'mean': individual_values.mean(),
            'std': individual_values.std()
        }

        if groups is None:
            return total_results, None

        group_results = dict()
        grouping = get_groupings(groups)
        for label, index in grouping.items():
            group_scores = individual_values[index]
            group_results[label] = {
                'mean': group_scores.mean(),
                'std': group_scores.std()
            }
        return total_results, group_results

    def reset(self):
        self.individual_values = []


class SSIMScore(PairwiseScore):
    def __init__(self, window_size=11):
        super().__init__()
        self.score = SSIM(window_size=window_size, size_average=False).eval()
        self.reset()

    def forward(self, pred_batch, target_batch, mask=None):
        batch_values = self.score(pred_batch, target_batch)
        self.individual_values = np.hstack([
            self.individual_values, batch_values.detach().cpu().numpy()
        ])
        return batch_values


class LPIPSScore(PairwiseScore):
    def __init__(self, model='net-lin', net='vgg', model_path=None, use_gpu=True):
        super().__init__()
        self.score = PerceptualLoss(model=model, net=net, model_path=model_path,
                                    use_gpu=use_gpu, spatial=False).eval()
        self.reset()

    def forward(self, pred_batch, target_batch, mask=None):
        batch_values = self.score(pred_batch, target_batch).flatten()
        self.individual_values = np.hstack([
            self.individual_values, batch_values.detach().cpu().numpy()
        ])
        return batch_values


def fid_calculate_activation_statistics(act):
    mu = np.mean(act, axis=0)
    sigma = np.cov(act, rowvar=False)
    return mu, sigma


def calculate_frechet_distance(activations_pred, activations_target, eps=1e-6):
    mu1, sigma1 = fid_calculate_activation_statistics(activations_pred)
    mu2, sigma2 = fid_calculate_activation_statistics(activations_target)

    diff = mu1 - mu2

    # Product might be almost singular
    covmean, _ = linalg.sqrtm(sigma1.dot(sigma2), disp=False)
    if not np.isfinite(covmean).all():
        msg = ('fid calculation produces singular product; '\
               'adding %s to diagonal of cov estimates') % eps
        LOGGER.warning(msg)
        offset = np.eye(sigma1.shape[0]) * eps
        covmean = linalg.sqrtm((sigma1 + offset).dot(sigma2 + offset))

    # Numerical error might give slight imaginary component
    if np.iscomplexobj(covmean):
        # if not np.allclose(np.diagonal(covmean).imag, 0, atol=1e-3):
        if not np.allclose(np.diagonal(covmean).imag, 0, atol=1e-2):
            m = np.max(np.abs(covmean.imag))
            raise ValueError('Imaginary component {}'.format(m))
        covmean = covmean.real

    tr_covmean = np.trace(covmean)

    return (diff.dot(diff) + np.trace(sigma1) +\
            np.trace(sigma2) - 2 * tr_covmean)


class FIDScore(EvaluatorScore):
    def __init__(self, dims=2048, eps=1e-6):
        LOGGER.info("FIDscore init called")
        super().__init__()
        if getattr(FIDScore, '_MODEL', None) is None:
            block_idx = InceptionV3.BLOCK_INDEX_BY_DIM[dims]
            FIDScore._MODEL = InceptionV3([block_idx]).eval()
        self.model = FIDScore._MODEL
        self.eps = eps
        self.reset()
        LOGGER.info("FIDscore init done")

    def forward(self, pred_batch, target_batch, mask=None):
        activations_pred = self._get_activations(pred_batch)
        activations_target = self._get_activations(target_batch)

        self.activations_pred.append(activations_pred.detach().cpu())
        self.activations_target.append(activations_target.detach().cpu())

        return activations_pred, activations_target

    def get_value(self, groups=None, states=None):
        LOGGER.info("FIDscore get_value called")
        activations_pred, activations_target = zip(*states) if states is not None \
            else (self.activations_pred, self.activations_target)
        activations_pred = torch.cat(activations_pred).cpu().numpy()
        activations_target = torch.cat(activations_target).cpu().numpy()

        total_distance = calculate_frechet_distance(activations_pred, activations_target, eps=self.eps)
        total_results = dict(mean=total_distance)

        if groups is None:
            group_results = None
        else:
            group_results = dict()
            grouping = get_groupings(groups)
            for label, index in grouping.items():
                if len(index) > 1:
                    group_distance = calculate_frechet_distance(activations_pred[index], activations_target[index],
                                                                eps=self.eps)
                    group_results[label] = dict(mean=group_distance)

                else:
                    group_results[label] = dict(mean=float('nan'))

        self.reset()

        LOGGER.info("FIDscore get_value done")

        return total_results, group_results

    def reset(self):
        self.activations_pred = []
        self.activations_target = []

    def _get_activations(self, batch):
        activations = self.model(batch)[0]
        if activations.shape[2] != 1 or activations.shape[3] != 1:
            assert False, \
                'We should not have got here, because Inception always scales inputs to 299x299'
            # activations = F.adaptive_avg_pool2d(activations, output_size=(1, 1))
        activations = activations.squeeze(-1).squeeze(-1)
        return activations


def get_groupings(groups):
    """
    :param groups: group numbers for respective elements
    :return: dict of kind {group_idx: indices of the corresponding group elements}
    """
    label_groups, count_groups = np.unique(groups, return_counts=True)

    indices = np.argsort(groups)

    grouping = dict()
    cur_start = 0
    for label, count in zip(label_groups, count_groups):
        cur_end = cur_start + count
        cur_indices = indices[cur_start:cur_end]
        grouping[label] = cur_indices
        cur_start = cur_end
    return grouping