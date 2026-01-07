import { Button } from "@/components/ui/button"
import { useNavigate } from "react-router-dom"
import { ArrowRight, FileText, Sparkles, Zap } from "lucide-react"

export default function LandingPage() {
    const navigate = useNavigate()

    return (
        <div className="flex min-h-screen flex-col bg-background">
            <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="container flex h-14 items-center">
                    <div className="flex items-center space-x-2 font-bold text-xl">
                        <FileText className="h-6 w-6" />
                        <span>Article ReAngle</span>
                    </div>
                    <nav className="ml-auto flex gap-4 sm:gap-6">
                        {/* Nav links could go here */}
                    </nav>
                </div>
            </header>
            <main className="flex-1">
                <section className="space-y-6 pb-8 pt-6 md:pb-12 md:pt-10 lg:py-32">
                    <div className="container flex max-w-[64rem] flex-col items-center gap-4 text-center">
                        <h1 className="font-heading text-3xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tighter">
                            Transform Your Content with{" "}
                            <span className="bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
                                AI Precision
                            </span>
                        </h1>
                        <p className="max-w-[42rem] leading-normal text-muted-foreground sm:text-xl sm:leading-8">
                            Intelligent rewriting, summarization, and content optimization.
                            Keep the core message, but change the angle.
                        </p>
                        <div className="space-x-4">
                            <Button size="lg" onClick={() => navigate("/app")}>
                                Get Started
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                </section>

                <section className="container space-y-6 py-8 md:py-12 lg:py-24">
                    <div className="mx-auto grid justify-center gap-4 sm:grid-cols-2 md:max-w-[64rem] md:grid-cols-3">
                        <div className="relative overflow-hidden rounded-lg border bg-background p-2">
                            <div className="flex h-[180px] flex-col justify-between rounded-md p-6">
                                <Sparkles className="h-12 w-12 text-primary" />
                                <div className="space-y-2">
                                    <h3 className="font-bold">Smart Rewrite</h3>
                                    <p className="text-sm text-muted-foreground">
                                        Adapt content to any style or tone with advanced LLMs like GPT-5 and Gemini.
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="relative overflow-hidden rounded-lg border bg-background p-2">
                            <div className="flex h-[180px] flex-col justify-between rounded-md p-6">
                                <FileText className="h-12 w-12 text-primary" />
                                <div className="space-y-2">
                                    <h3 className="font-bold">Multi-Format</h3>
                                    <p className="text-sm text-muted-foreground">
                                        Process text files, PDFs, Word docs, URLs, and even YouTube videos.
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div className="relative overflow-hidden rounded-lg border bg-background p-2">
                            <div className="flex h-[180px] flex-col justify-between rounded-md p-6">
                                <Zap className="h-12 w-12 text-primary" />
                                <div className="space-y-2">
                                    <h3 className="font-bold">Instant Analysis</h3>
                                    <p className="text-sm text-muted-foreground">
                                        Get summaries, comparisons, and readability metrics in seconds.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </section>
            </main>
            <footer className="py-6 md:px-8 md:py-0">
                <div className="container flex flex-col items-center justify-between gap-4 md:h-24 md:flex-row">
                    <p className="text-center text-sm leading-loose text-muted-foreground md:text-left">
                        Built by Article ReAngle Team.
                    </p>
                </div>
            </footer>
        </div>
    )
}
