export function isMalaysianNationality(value: string | null | undefined) {
  return ["malaysia", "malaysian"].includes(String(value ?? "").trim().toLowerCase())
}

export function identityNumberLabel(nationality: string | null | undefined) {
  return isMalaysianNationality(nationality) ? "Identity number" : "Passport Number"
}
