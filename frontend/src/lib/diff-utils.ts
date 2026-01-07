export interface DiffPart {
    type: 'equal' | 'insert' | 'delete' | 'replace';
    text: string;
}

export interface AlignedParagraphPair {
    original: string;
    rewritten: string;
}

/**
 * Splits text into paragraphs using intelligent logic.
 */
export function splitIntoParagraphs(text: string): string[] {
    if (!text) return [];

    // Clean text
    let cleaned = text.replace(/\s+/g, ' ').trim();

    // Split by double newline first
    let paragraphs = cleaned.split(/\n\s*\n/);

    // If single paragraph, try intelligent split
    if (paragraphs.length === 1) {
        paragraphs = intelligentParagraphSplit(cleaned);
    }

    // Optimize segmentation
    paragraphs = optimizeParagraphSegmentation(paragraphs);

    return paragraphs.map(p => p.trim()).filter(p => p.length > 0);
}

function intelligentParagraphSplit(text: string): string[] {
    const paragraphs: string[] = [];
    const sentences = text.split(/([。！？；])/);
    let currentPara = '';
    let sentenceCount = 0;

    for (let i = 0; i < sentences.length; i += 2) {
        const sentence = sentences[i];
        const punctuation = sentences[i + 1] || '';

        if (sentence.trim()) {
            currentPara += sentence.trim() + punctuation;
            sentenceCount++;

            // Split conditions: >3 sentences AND (>150 chars OR has marker)
            const shouldSplit = (
                sentenceCount >= 3 &&
                (currentPara.length > 150 || hasParagraphMarker(currentPara))
            );

            if (shouldSplit) {
                paragraphs.push(currentPara.trim());
                currentPara = '';
                sentenceCount = 0;
            }
        }
    }

    if (currentPara.trim()) {
        paragraphs.push(currentPara.trim());
    }

    return paragraphs;
}

function hasParagraphMarker(text: string): boolean {
    const markers = [
        '首先', '其次', '再次', '最后', '总之', '综上所述',
        '另外', '此外', '同时', '然而', '但是', '不过',
        '因此', '所以', '由此可见', '总的来说', '简而言之'
    ];
    return markers.some(marker => text.includes(marker));
}

function optimizeParagraphSegmentation(paragraphs: string[]): string[] {
    const optimized: string[] = [];

    for (const para of paragraphs) {
        if (para.length > 500) {
            optimized.push(...splitLongParagraph(para));
        } else {
            optimized.push(para);
        }
    }
    return optimized;
}

function splitLongParagraph(text: string): string[] {
    const sentences = text.split(/([。！？；])/);
    const subParagraphs: string[] = [];
    let currentPara = '';
    let sentenceCount = 0;

    for (let i = 0; i < sentences.length; i += 2) {
        const sentence = sentences[i];
        const punctuation = sentences[i + 1] || '';

        if (sentence.trim()) {
            currentPara += sentence.trim() + punctuation;
            sentenceCount++;

            if (sentenceCount >= 2 && currentPara.length > 200) {
                subParagraphs.push(currentPara.trim());
                currentPara = '';
                sentenceCount = 0;
            }
        }
    }

    if (currentPara.trim()) {
        subParagraphs.push(currentPara.trim());
    }
    return subParagraphs;
}

/**
 * Aligns original and rewritten paragraphs side-by-side.
 */
export function alignParagraphs(originalText: string, rewrittenText: string): AlignedParagraphPair[] {
    const originalParagraphs = splitIntoParagraphs(originalText);
    const rewrittenParagraphs = splitIntoParagraphs(rewrittenText);

    const alignedPairs: AlignedParagraphPair[] = [];
    const maxParagraphs = Math.max(originalParagraphs.length, rewrittenParagraphs.length);

    for (let i = 0; i < maxParagraphs; i++) {
        alignedPairs.push({
            original: originalParagraphs[i] || '',
            rewritten: rewrittenParagraphs[i] || '',
        });
    }

    return alignedPairs;
}

/**
 * Computes word-level diff between two texts.
 * Returns array of parts to be rendered.
 */
export function computeSmartDiff(text1: string, text2: string): DiffPart[] {
    if (!text1) return [{ type: 'insert', text: text2 }];
    if (!text2) return [{ type: 'delete', text: text1 }];

    const words1 = text1.split(/(\s+|[，。！？；：""''（）【】])/);
    const words2 = text2.split(/(\s+|[，。！？；：""''（）【】])/);

    const diff: DiffPart[] = [];
    let i = 0, j = 0;

    // Simple heuristic diff (greedy matching)
    // This is a simplified port of the original logic which was also somewhat greedy
    while (i < words1.length || j < words2.length) {
        if (i >= words1.length) {
            diff.push({ type: 'insert', text: words2[j] });
            j++;
        } else if (j >= words2.length) {
            diff.push({ type: 'delete', text: words1[i] });
            i++;
        } else if (words1[i] === words2[j]) {
            diff.push({ type: 'equal', text: words1[i] });
            i++;
            j++;
        } else {
            // Lookahead to resync
            let foundMatch = false;
            // Check if words2[j] appears later in words1 (insertion)
            // Check if words1[i] appears later in words2 (deletion)
            // Simplified: just mark as replace for single word mismatch or insert/delete

            // Try to find words1[i] in upcoming words2
            const kMax = Math.min(words2.length, j + 5);
            for (let k = j + 1; k < kMax; k++) {
                if (words2[k] === words1[i]) {
                    // Found match later in V2 -> Implicit Insertions before it
                    while (j < k) {
                        diff.push({ type: 'insert', text: words2[j] });
                        j++;
                    }
                    foundMatch = true;
                    break;
                }
            }

            if (foundMatch) continue;

            // Try to find words2[j] in upcoming words1
            const mMax = Math.min(words1.length, i + 5);
            for (let m = i + 1; m < mMax; m++) {
                if (words1[m] === words2[j]) {
                    // Found match later in V1 -> Implicit Deletions before it
                    while (i < m) {
                        diff.push({ type: 'delete', text: words1[i] });
                        i++;
                    }
                    foundMatch = true;
                    break;
                }
            }

            if (foundMatch) continue;

            // If no resync found, treat as replace (delete + insert)
            // Or simplified: just take the new one as insert and old as delete
            // The original logic was:
            /*
            diff.push({ type: 'delete', text: words1[i] });
            i++;
            */
            // But visually we often want 'change'.
            // Let's stick to simple insert/delete if completely different.
            diff.push({ type: 'delete', text: words1[i] });
            diff.push({ type: 'insert', text: words2[j] });
            i++;
            j++;
        }
    }

    return diff;
}
