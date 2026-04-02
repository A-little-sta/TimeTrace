import logging
import torch
from saicinpainting.training.trainers.default import DefaultInpaintingTrainingModule


def get_training_model_class(kind):
    if kind == 'default':
        return DefaultInpaintingTrainingModule

    raise ValueError(f'Unknown trainer module {kind}')


def make_training_model(config):
    kind = config.training_model.kind
    kwargs = dict(config.training_model)
    kwargs.pop('kind')
    
    # 移除构造函数不接受的参数，只保留BaseInpaintingTrainingModule.__init__实际接受的参数
    # BaseInpaintingTrainingModule.__init__接受的参数：config, use_ddp, predict_only, visualize_each_iters, 
    # average_generator, generator_avg_beta, average_generator_start_step, average_generator_period, store_discr_outputs_for_vis
    accepted_params = ['use_ddp', 'predict_only', 'visualize_each_iters', 
                      'average_generator', 'generator_avg_beta', 
                      'average_generator_start_step', 'average_generator_period', 
                      'store_discr_outputs_for_vis']
    
    # 过滤kwargs，只保留accepted_params中的参数
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in accepted_params}
    
    # 处理 trainer 字段可能不存在的情况
    try:
        filtered_kwargs['use_ddp'] = config.trainer.kwargs.get('accelerator', None) == 'ddp'
    except (AttributeError, KeyError):
        filtered_kwargs['use_ddp'] = False

    # 设置默认的predict_only为True，因为我们只是在进行推理
    filtered_kwargs['predict_only'] = True

    logging.info(f'Make training model {kind}')
    logging.info(f'Filtered kwargs: {filtered_kwargs}')

    cls = get_training_model_class(kind)
    return cls(config, **filtered_kwargs)


def load_checkpoint(train_config, path, map_location='cuda', strict=True):
    model: torch.nn.Module = make_training_model(train_config)
    state = torch.load(path, map_location=map_location)
    model.load_state_dict(state['state_dict'], strict=strict)
    model.on_load_checkpoint(state)
    return model
