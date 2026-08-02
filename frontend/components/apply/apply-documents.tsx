"use client"

import Link from "next/link"
import { useEffect, useMemo, useState } from "react"
import { Upload } from "lucide-react"

import { Header } from "@/components/layout/header"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import {
  loadApplyApplications,
  loadApplyOptions,
  uploadApplyDocument,
  type ApplyApplication,
  type ApplyOptions,
} from "@/lib/apply"

const inputClass =
  "h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs outline-none transition focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px]"
const IMAGE_DOCUMENT_TYPES = new Set(["passport", "photo"])
const ALLOWED_IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"]
const IMAGE_ACCEPT = ALLOWED_IMAGE_EXTENSIONS.join(",")

function fileExtension(filename: string) {
  const dotIndex = filename.lastIndexOf(".")
  return dotIndex >= 0 ? filename.slice(dotIndex).toLowerCase() : ""
}

function optionLabel(options: ApplyOptions | null, value: string) {
  return options?.document_types.find((item) => item.value === value)?.label ?? value
}

export function ApplyDocuments() {
  const [applications, setApplications] = useState<ApplyApplication[]>([])
  const [options, setOptions] = useState<ApplyOptions | null>(null)
  const [documentType, setDocumentType] = useState("passport")
  const [file, setFile] = useState<File | null>(null)
  const [message, setMessage] = useState("")
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(true)
  const [isUploading, setIsUploading] = useState(false)

  useEffect(() => {
    let isMounted = true

    async function load() {
      try {
        const [nextOptions, nextApplications] = await Promise.all([
          loadApplyOptions(),
          loadApplyApplications(),
        ])
        if (!isMounted) return
        setOptions(nextOptions)
        setApplications(nextApplications)
        setDocumentType(nextOptions.document_types[0]?.value ?? "passport")
      } catch (caught) {
        if (isMounted) setError(caught instanceof Error ? caught.message : "Unable to load documents")
      } finally {
        if (isMounted) setIsLoading(false)
      }
    }

    void load()
    return () => {
      isMounted = false
    }
  }, [])

  const application = applications[0]
  const documents = useMemo(() => application?.documents ?? [], [application?.documents])
  const requiredDocuments = options?.admissions_setup.required_documents ?? []
  const uploadedDocumentTypes = useMemo(
    () => new Set(documents.map((document) => document.document_type)),
    [documents]
  )

  async function handleUpload(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!application || !file) return
    setMessage("")
    setError("")
    if (IMAGE_DOCUMENT_TYPES.has(documentType)) {
      const extension = fileExtension(file.name)
      if (!ALLOWED_IMAGE_EXTENSIONS.includes(extension)) {
        setError("Identity and photo documents must be jpg, jpeg, png, webp, heic, or heif images.")
        return
      }
    }
    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.set("document_type", documentType)
      formData.set("file", file)
      await uploadApplyDocument(application.id, formData)
      const nextApplications = await loadApplyApplications()
      setApplications(nextApplications)
      setFile(null)
      setMessage("Document uploaded.")
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to upload document")
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="flex min-h-svh flex-col bg-muted/25">
      <Header
        breadcrumbItems={[
          { href: "/apply", title: "Apply" },
          { href: "/apply/documents", title: "Documents" },
        ]}
      />
      <main className="flex-1 space-y-6 px-4 pb-8 pt-4 sm:px-6">
        <section className="border-b border-border/70 pb-5">
          <p className="text-sm font-semibold text-teal-700 dark:text-teal-300">Documents Upload</p>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight sm:text-3xl">
            Supporting Documents
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-muted-foreground">
            Upload files against the latest draft or submitted application.
          </p>
        </section>

        {message ? (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm font-medium text-emerald-700">
            {message}
          </div>
        ) : null}
        {error ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm font-medium text-red-700">
            {error}
          </div>
        ) : null}

        {!isLoading && !application ? (
          <div className="rounded-lg border border-border bg-background p-5 shadow-sm">
            <p className="text-sm text-muted-foreground">
              Save an application draft before uploading documents.
            </p>
            <Button className="mt-4" render={<Link href="/apply/application" />}>
              Open Application Form
            </Button>
          </div>
        ) : null}

        {application ? (
          <section className="grid gap-5 lg:grid-cols-[24rem_minmax(0,1fr)]">
            <form
              className="rounded-lg border border-border bg-background p-5 shadow-sm"
              onSubmit={handleUpload}
            >
              <h2 className="text-lg font-semibold">Upload New File</h2>
              <div className="mt-4 space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="document_type">Document type</Label>
                  <select
                    id="document_type"
                    className={inputClass}
                    value={documentType}
                    onChange={(event) => setDocumentType(event.target.value)}
                  >
                    {(options?.document_types ?? []).map((item) => (
                      <option key={item.value} value={item.value}>{item.label}</option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="file">File</Label>
                  <input
                    id="file"
                    type="file"
                    accept={IMAGE_DOCUMENT_TYPES.has(documentType) ? IMAGE_ACCEPT : undefined}
                    className="block w-full text-sm text-muted-foreground file:mr-3 file:rounded-md file:border-0 file:bg-teal-700 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white"
                    onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                    required
                  />
                </div>
                <Button type="submit" disabled={isUploading || !file}>
                  <Upload className="size-4" />
                  {isUploading ? "Uploading..." : "Upload Document"}
                </Button>
              </div>
            </form>

            <div className="space-y-5">
              {requiredDocuments.length ? (
                <div className="rounded-lg border border-border bg-background p-5 shadow-sm">
                  <h2 className="text-lg font-semibold">Required Documents</h2>
                  <div className="mt-4 grid gap-3">
                    {requiredDocuments.map((documentType) => {
                      const uploaded = uploadedDocumentTypes.has(documentType)
                      return (
                        <div
                          key={documentType}
                          className="flex flex-col gap-2 rounded-lg border border-border p-3 sm:flex-row sm:items-center sm:justify-between"
                        >
                          <p className="text-sm font-medium">{optionLabel(options, documentType)}</p>
                          <Badge variant={uploaded ? "secondary" : "outline"}>
                            {uploaded ? "Uploaded" : "Required"}
                          </Badge>
                        </div>
                      )
                    })}
                  </div>
                </div>
              ) : null}

              <div className="rounded-lg border border-border bg-background p-5 shadow-sm">
                <h2 className="text-lg font-semibold">Uploaded Documents</h2>
                <div className="mt-4 grid gap-3">
                  {documents.length ? (
                    documents.map((document) => (
                      <div key={document.id} className="rounded-lg border border-border p-3">
                        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                          <p className="text-sm font-medium">{document.original_name || optionLabel(options, document.document_type)}</p>
                          <span className="w-fit rounded-md bg-muted px-2 py-1 text-xs font-semibold">
                            {document.status}
                          </span>
                        </div>
                        <p className="mt-1 text-xs text-muted-foreground">{optionLabel(options, document.document_type)}</p>
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-muted-foreground">No documents uploaded yet.</p>
                  )}
                </div>
              </div>
            </div>
          </section>
        ) : null}
      </main>
    </div>
  )
}
