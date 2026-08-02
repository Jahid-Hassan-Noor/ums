type OptimisticUpdateOptions<TSnapshot, TResult> = {
  snapshot: () => TSnapshot
  apply: (snapshot: TSnapshot) => void
  request: () => Promise<TResult>
  commit?: (result: TResult, snapshot: TSnapshot) => void
  rollback: (snapshot: TSnapshot) => void
}

export async function runOptimisticUpdate<TSnapshot, TResult>({
  snapshot,
  apply,
  request,
  commit,
  rollback,
}: OptimisticUpdateOptions<TSnapshot, TResult>) {
  const previous = snapshot()
  apply(previous)

  try {
    const result = await request()
    commit?.(result, previous)
    return result
  } catch (error) {
    rollback(previous)
    throw error
  }
}
