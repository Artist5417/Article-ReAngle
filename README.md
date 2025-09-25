# Article ReAngle

A local web app powered by LLMs that rewrites articles while preserving key information, enabling users to generate new versions with customizable style, perspective, and viewpoints.

---

## 1. Program Overview

This program is a **localhost web application** powered by **Large Language Models (LLMs)**.  
Core objectives:  

- Preserve the main information of the article  
- Adjust **style/perspective** according to user requirements  
- Generate a newly expressed version of the article  

Supported input methods: paste text / upload files / provide URL.  
Output methods: online reading, export as Word/PDF/Markdown.  

---

## 2. Input and Preprocessing

### Input Methods

1. **Paste text directly**  
2. **Upload files** (TXT / Word / PDF)  
3. **Enter article URL** (automatically extract the main body)  

### Preprocessing Logic

- **Word** → Extract body paragraphs  
- **PDF** → Parse text layer; if scanned, call OCR to extract text  
- **URL** → Extract main content and filter ads, navigation bars, etc.  

All inputs are eventually unified into **structured plain text**, ready for model processing.  

---

## 3. Model Processing Logic

Adopts a “two-step” strategy:  

1. **Key Point Extraction**  
   - Use LLM to summarize the article, extract core information and logical framework  
   - Ensure content fidelity, complete structure, and neutral stance  

2. **Perspective Rewriting**  
   - Combine extracted key points with user prompts  
   - User prompts support:  
     - **Style control** (academic / news reporting / humorous)  
     - **Perspective control** (supporting a policy / consumer’s viewpoint, etc.)  
   - Output a new article reflecting the chosen perspective  

---

## 4. Output and Display

### Display Options

- Direct reading on the web page  
- **Comparison view** between original and rewritten article (with similarity calculation)  

### Export Formats

- Word  
- PDF  
- Markdown / HTML  

---

## 5. User Interface and Interaction

- **Homepage functions**: paste text / upload file / enter URL  
- **Prompt input**: freeform entry & preset templates (academic, news, humorous, etc.)  
- **Rewrite intensity adjustment**: from light editing → full rewrite  
- **User experience**: progress display after submission → result page → read / compare / download  

---

## 6. Extended Features and Future Plans

- **API interface**: support for external system integration  
- **Logs & optimization**: keep processing logs (de-identified), useful for debugging and improvement  
- **Risk alerts**: notify users of compliance when dealing with sensitive or controversial topics  
- **Future plans**: expand into plugins (Word plugin, browser extension)  

---

## License

[MIT](LICENSE)
