type AdapterWithFallback = GPUAdapter & {
  isFallbackAdapter?: boolean
}

export async function getUsableWebGpuAdapter() {
  if (!('gpu' in navigator)) return false
  const adapter = (await navigator.gpu.requestAdapter()) as AdapterWithFallback | null
  if (!adapter || adapter.isFallbackAdapter) return false
  return adapter
}

export async function hasUsableWebGpu() {
  return Boolean(await getUsableWebGpuAdapter())
}
