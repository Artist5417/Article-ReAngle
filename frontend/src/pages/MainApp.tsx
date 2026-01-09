import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { DiffView } from "@/components/DiffView"
import { Loader2, Trash2, FileText, Link as LinkIcon, Youtube, Type, Play, Download } from "lucide-react"

// Types
interface InputItem {
    id: string
    type: 'text' | 'file' | 'url' | 'youtube'
    content?: string | File
    meta?: {
        title: string
        detail: string
    }
}

interface RewriteResult {
    original: string
    rewritten: string
    summary: string
}

export default function MainApp() {
    // State
    const [activeInputTab, setActiveInputTab] = useState("text")
    const [inputItems, setInputItems] = useState<InputItem[]>([])

    // Inputs
    const [inputText, setInputText] = useState("")
    const [inputUrl, setInputUrl] = useState("")
    const [inputFile, setInputFile] = useState<File | null>(null)

    // Settings
    const [prompt, setPrompt] = useState("")
    const [model, setModel] = useState("gpt-5")
    const [isLoading, setIsLoading] = useState(false)

    // Result
    const [result, setResult] = useState<RewriteResult | null>(null)
    const [activeResultTab, setActiveResultTab] = useState("summary")
    const [error, setError] = useState<string | null>(null)

    // TTS State
    const [ttsLoading, setTtsLoading] = useState(false)
    const [audioUrl, setAudioUrl] = useState<string | null>(null)
    const audioRef = useRef<HTMLAudioElement | null>(null)

    // Handlers
    const handleAddInput = () => {
        const id = Math.random().toString(36).substring(7)
        let newItem: InputItem | null = null

        if (activeInputTab === "text" && inputText.trim()) {
            newItem = {
                id, type: "text", content: inputText,
                meta: { title: "Text Snippet", detail: `${inputText.length} chars` }
            }
            setInputText("")
        } else if (activeInputTab === "url" && inputUrl.trim()) {
            newItem = {
                id, type: "url", content: inputUrl,
                meta: { title: "URL", detail: inputUrl }
            }
            setInputUrl("")
        } else if (activeInputTab === "youtube" && inputUrl.trim()) {
            newItem = {
                id, type: "youtube", content: inputUrl,
                meta: { title: "YouTube", detail: inputUrl }
            }
            setInputUrl("")
        } else if (activeInputTab === "file" && inputFile) {
            newItem = {
                id, type: "file", content: inputFile,
                meta: { title: inputFile.name, detail: `${(inputFile.size / 1024).toFixed(1)} KB` }
            }
            setInputFile(null)
            // Reset file input value manually if needed via ref, simpler here
        }

        if (newItem) {
            setInputItems([...inputItems, newItem])
        }
    }

    const handleRemoveInput = (id: string) => {
        setInputItems(inputItems.filter(i => i.id !== id))
    }

    const handleProcess = async () => {
        if (inputItems.length === 0) {
            setError("Please add at least one input item.")
            return
        }

        setIsLoading(true)
        setError(null)
        setResult(null)
        setAudioUrl(null)

        try {
            const formData = new FormData()

            // Construct payload
            const payloadItems = inputItems.map(item => {
                if (item.type === 'file') {
                    const fileKey = `file_${item.id}`
                    formData.append(fileKey, item.content as File)
                    return {
                        id: item.id,
                        type: item.type,
                        contentKey: fileKey,
                        meta: { filename: (item.content as File).name }
                    }
                } else {
                    return {
                        id: item.id,
                        type: item.type,
                        content: item.content
                    }
                }
            })

            formData.append("inputs", JSON.stringify(payloadItems))
            formData.append("prompt", prompt)
            formData.append("llm_type", model)

            const res = await fetch("/api/v1/rewrite", {
                method: "POST",
                body: formData
            })

            if (!res.ok) {
                throw new Error(`Server error: ${res.status}`)
            }

            const data = await res.json()
            setResult(data)
            setActiveResultTab("summary") // Switch to summary on success

        } catch (err: any) {
            console.error(err)
            setError(err.message || "Failed to process request")
        } finally {
            setIsLoading(false)
        }
    }

    const handlePreset = (preset: string) => {
        setPrompt(preset)
    }

    const handlePlayTTS = async () => {
        if (!result?.summary) return
        if (audioUrl) {
            audioRef.current?.play()
            return
        }

        if (result.summary.length > 600) {
            alert("Summary is too long for Read Aloud (max 600 characters).")
            return
        }

        setTtsLoading(true)
        try {
            const res = await fetch("/api/v1/rewrite/tts", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text: result.summary })
            })

            if (!res.ok) throw new Error("TTS failed")

            const data = await res.json()
            setAudioUrl(data.audio_url)
            // Audio will be rendered below, user can click play
        } catch (err) {
            console.error("TTS Error:", err)
        } finally {
            setTtsLoading(false)
        }
    }

    const handleDownload = () => {
        if (!result?.rewritten) return

        const element = document.createElement("a")
        const file = new Blob([result.rewritten], { type: 'text/plain' })
        element.href = URL.createObjectURL(file)
        element.download = "rewritten_article.txt"
        document.body.appendChild(element)
        element.click()
        document.body.removeChild(element)
    }

    return (
        <div className="flex h-screen flex-col bg-background text-foreground">
            <header className="border-b bg-background/95 backdrop-blur z-10">
                <div className="container flex h-14 items-center px-4">
                    <div className="font-bold flex items-center gap-2">
                        <FileText className="w-5 h-5" /> Article ReAngle
                    </div>
                    <div className="ml-auto text-sm text-muted-foreground">
                        Dashboard
                    </div>
                </div>
            </header>

            <main className="flex-1 container py-6 flex flex-col lg:flex-row gap-6 overflow-hidden h-full">
                {/* Left Pane: Inputs & Settings */}
                <div className="w-full lg:w-4/12 flex flex-col gap-6 overflow-y-auto pr-2 pb-20">

                    {/* Input Section */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Input Sources</CardTitle>
                            <CardDescription>Add text, files, or links to process.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <Tabs value={activeInputTab} onValueChange={setActiveInputTab} className="w-full">
                                <TabsList className="grid w-full grid-cols-4">
                                    <TabsTrigger value="text"><Type className="w-4 h-4" /></TabsTrigger>
                                    <TabsTrigger value="file"><FileText className="w-4 h-4" /></TabsTrigger>
                                    <TabsTrigger value="url"><LinkIcon className="w-4 h-4" /></TabsTrigger>
                                    <TabsTrigger value="youtube"><Youtube className="w-4 h-4" /></TabsTrigger>
                                </TabsList>

                                <div className="p-4 border rounded-md mt-2 bg-muted/20">
                                    {activeInputTab === 'text' && (
                                        <Textarea
                                            placeholder="Paste text here..."
                                            className="min-h-[100px]"
                                            value={inputText}
                                            onChange={e => setInputText(e.target.value)}
                                        />
                                    )}
                                    {(activeInputTab === 'url' || activeInputTab === 'youtube') && (
                                        <Input
                                            placeholder={activeInputTab === 'url' ? "https://example.com/article" : "https://youtube.com/watch?v=..."}
                                            value={inputUrl}
                                            onChange={e => setInputUrl(e.target.value)}
                                        />
                                    )}
                                    {activeInputTab === 'file' && (
                                        <div className="grid w-full max-w-sm items-center gap-1.5">
                                            <Label htmlFor="file">File</Label>
                                            <Input id="file" type="file" onChange={e => setInputFile(e.target.files?.[0] || null)} />
                                            <p className="text-xs text-muted-foreground">Supported: TXT, PDF, DOCX</p>
                                        </div>
                                    )}

                                    <Button className="w-full mt-4" variant="secondary" onClick={handleAddInput}>
                                        Add to Basket
                                    </Button>
                                </div>
                            </Tabs>

                            {/* Basket */}
                            <div className="space-y-2">
                                <Label>Selected Inputs ({inputItems.length})</Label>
                                <div className="space-y-2 max-h-[150px] overflow-y-auto p-1">
                                    {inputItems.map(item => (
                                        <div key={item.id} className="flex items-center justify-between p-2 border rounded text-sm bg-card">
                                            <div className="truncate flex-1 pr-2">
                                                <div className="font-medium truncate">{item.meta?.title}</div>
                                                <div className="text-xs text-muted-foreground truncate">{item.meta?.detail}</div>
                                            </div>
                                            <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive" onClick={() => handleRemoveInput(item.id)}>
                                                <Trash2 className="h-3 w-3" />
                                            </Button>
                                        </div>
                                    ))}
                                    {inputItems.length === 0 && (
                                        <div className="text-sm text-muted-foreground text-center py-4 border border-dashed rounded">
                                            Basket is empty
                                        </div>
                                    )}
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Settings Section */}
                    <Card>
                        <CardHeader>
                            <CardTitle>Configuration</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="space-y-2">
                                <Label>Model</Label>
                                <Select value={model} onValueChange={setModel}>
                                    <SelectTrigger>
                                        <SelectValue placeholder="Select model" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="gpt-5">GPT-5 (Best Quality)</SelectItem>
                                        <SelectItem value="gemini-2.5-flash">Gemini 2.5 Flash</SelectItem>
                                        <SelectItem value="qwen-flash">Qwen Flash</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>

                            <div className="space-y-2">
                                <div className="flex justify-between">
                                    <Label>Style Instructions</Label>
                                    <Select onValueChange={handlePreset}>
                                        <SelectTrigger className="h-6 w-[120px] text-xs">
                                            <SelectValue placeholder="Presets" />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="Humorous Tone">Humorous</SelectItem>
                                            <SelectItem value="Academic Tone">Academic</SelectItem>
                                            <SelectItem value="Journalistic Tone">Journalistic</SelectItem>
                                            <SelectItem value="Blog style">Blog Post</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                                <Textarea
                                    placeholder="e.g. Make it more professional..."
                                    value={prompt}
                                    onChange={e => setPrompt(e.target.value)}
                                />
                            </div>

                            <Button size="lg" className="w-full font-bold shadow-lg shadow-primary/20" onClick={handleProcess} disabled={isLoading || inputItems.length === 0}>
                                {isLoading ? (
                                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Processing...</>
                                ) : (
                                    "Rewrite Content"
                                )}
                            </Button>

                            {error && (
                                <div className="text-sm text-destructive p-2 bg-destructive/10 rounded">
                                    Error: {error}
                                </div>
                            )}
                        </CardContent>
                    </Card>
                </div>

                {/* Right Pane: Results */}
                <div className="w-full lg:w-8/12 flex flex-col overflow-hidden h-full rounded-lg border bg-card shadow-sm">
                    {!result ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
                            <div className="p-8 rounded-full bg-muted mb-4">
                                <SparklesIcon className="w-8 h-8 opacity-20" />
                            </div>
                            <p>Process content to see results here.</p>
                        </div>
                    ) : (
                        <Tabs value={activeResultTab} onValueChange={setActiveResultTab} className="flex-1 flex flex-col h-full overflow-hidden">
                            <div className="border-b px-4 py-2 flex items-center bg-muted/30">
                                <TabsList>
                                    <TabsTrigger value="summary">Summary</TabsTrigger>
                                    <TabsTrigger value="rewritten">Rewritten</TabsTrigger>
                                    <TabsTrigger value="compare">Compare</TabsTrigger>
                                </TabsList>
                            </div>

                            <div className="flex-1 overflow-y-auto p-6">
                                <TabsContent value="summary" className="mt-0 h-full">
                                    <div className="prose dark:prose-invert max-w-none">
                                        <div className="flex items-center justify-between mb-4">
                                            <h3 className="text-xl font-bold m-0">Summary</h3>
                                            <div className="flex items-center gap-2">
                                                <div className="flex items-center gap-2">
                                                    {audioUrl ? (
                                                        <audio ref={audioRef} controls src={audioUrl} className="h-8 w-96" />
                                                    ) : (
                                                        <Button size="sm" variant="outline" onClick={handlePlayTTS} disabled={ttsLoading}>
                                                            {ttsLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 mr-2" />}
                                                            Read Aloud
                                                        </Button>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <p className="whitespace-pre-wrap">{result.summary}</p>
                                    </div>
                                </TabsContent>
                                <TabsContent value="rewritten" className="mt-0 h-full">
                                    <div className="prose dark:prose-invert max-w-none h-full flex flex-col">
                                        <div className="flex items-center justify-between mb-4">
                                            <h3 className="text-xl font-bold m-0">Rewritten Content</h3>
                                            <Button size="sm" variant="outline" onClick={handleDownload}>
                                                <Download className="w-4 h-4 mr-2" />
                                                Download TXT
                                            </Button>
                                        </div>
                                        <div className="whitespace-pre-wrap p-4 bg-background border rounded-md shadow-sm flex-1 overflow-auto">
                                            {result.rewritten}
                                        </div>
                                    </div>
                                </TabsContent>
                                <TabsContent value="compare" className="mt-0 h-full">
                                    <DiffView original={result.original} rewritten={result.rewritten} />
                                </TabsContent>
                            </div>
                        </Tabs>
                    )}
                </div>
            </main>
        </div>
    )
}

function SparklesIcon(props: any) {
    return (
        <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" /><path d="M5 3v4" /><path d="M9 3v4" /><path d="M7 6h4" /><path d="M3 7h4" /></svg>
    )
}
