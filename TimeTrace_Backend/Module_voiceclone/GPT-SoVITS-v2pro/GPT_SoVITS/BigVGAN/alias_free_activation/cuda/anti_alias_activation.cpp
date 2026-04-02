#include <torch/extension.h>

extern "C" torch::Tensor fwd_cuda(torch::Tensor const &input, torch::Tensor const &up_filter, torch::Tensor const &down_filter, torch::Tensor const &alpha, torch::Tensor const &beta);

PYBIND11_MODULE(TORCH_EXTENSION_NAME, m) {
    m.def("forward", &fwd_cuda, "Anti-Alias Activation forward (CUDA)");
}