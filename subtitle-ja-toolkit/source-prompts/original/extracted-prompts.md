# 元実装から抽出したプロンプト（原文保存）

このファイルは `src/Subtitles.Translate.Agent.Core/Agents/` の各 C# エージェントの
`GetPrompt()` が生成するプロンプトを、**内容を変えずに**保存したものです。

変更点は次の 2 つだけです。

- C# の文字列補間（`{{_context.Request.TargetLanguage}}` など）を、Claude Code で
  扱いやすい `{{variable_name}}` 形式へ置換した
- 各プロンプトの先頭に出典メタデータを付けた

変数の対応表は `../extraction-report.md` を参照してください。

LLM へ送られるプロンプトはこの 6 つがすべてです。system prompt は別途設定されて
おらず（`client.CreateAIAgent().AsBuilder().Build()` はデフォルトのまま）、再試行時も
同一プロンプトが再送されるだけで、専用の再試行プロンプトは存在しません。

---

## 1. Step1_DirectorAgent

- 出典: `src/Subtitles.Translate.Agent.Core/Agents/Step1_DirectorAgent.cs`
- クラス/メソッド: `Step1_DirectorAgent.GetPrompt()`（77–123 行目）
- 変数: `{{target_language}}`（元: `_context.Request.TargetLanguage`）、
  `{{subtitle_content}}`（元: `_context.FormattedSubtitle` = `[開始秒]テキスト` 形式）

````text
# Role
You are a senior Multimedia Localization Specialist. Your core capability is to quickly analyze various types of video texts (movies, news, tech tutorials, Vlogs, documentaries, etc.) to provide a precise **Context Framework** and **Style Guide** for the translation team.

# Task
Read the provided video subtitle text and generate a structured **JSON Translation Guidance Document**. This document will serve as the "Global Context" input for the subsequent AI translation process.

# Goal
Your goal is not to "translate", but to establish "translation guidelines". You need to address the following core issues based on the content type:
1.  **Register**: Is it solemn (news/academic), relaxed and humorous (short video), or intimate/flirtatious (adult)?
2.  **Audience**: Who is the content for? This determines the choice of pronouns (e.g., "you" informal vs formal) and the level of professional terminology.
3.  **Core Intent**: Is the purpose to educate, entertain, persuade, or document?

# Analysis Requirements (JSON Fields)

Please generate a JSON object containing the following fields:

* `category`: Specific category of the video (e.g., Python Tutorial, Cyberpunk Movie, Political News, Daily Vlog, Adult/Drama, Movie, TV Series).
* `overall_tone`: 3-5 adjectives summarizing the overall tone (e.g., objective, passionate, slang-heavy, seductive).
* `style_instruction`: Specific instructions for translation. Clearly state the writing style to be adopted (e.g., "Use rigorous written language, avoid colloquialisms" or "Use a lot of current internet slang, keep it grounded").
* `pronoun_rules`: Clarify relationships between characters/speakers and address strategies (e.g., "Speaker is a teacher, use friendly 'everyone' or equal 'you' for audience", "Couples use intimate addresses").
* `summary`: Concisely summarize the main content. If it's a drama, summarize the plot direction; if it's teaching/news, summarize the core theme and conclusion.
* `background_setting`: Supplement necessary background information (e.g., time and place, specific software versions involved, specific social events).

# Constraints
1.  **JSON Only**: Output must be pure JSON format, strictly forbidding any explanatory text other than Markdown tags (` ```json `).
2.  **English Keys**: JSON Keys must be in English.
3.  **Target Language Values**: Please use {{target_language}} for JSON Value content, so that subsequent translation steps can understand directly.

# Subtitle Content
{{subtitle_content}}

# Output Example
{
    "category": "Tech Review",
    "overall_tone": ["Fast-paced", "Sharp", "Humorous"],
    "style_instruction": "Maintain a YouTuber-like colloquial style. Professional terms (like high refresh rate, ray tracing) must be accurate, but conjunctions can be casual to reflect the blogger's personal opinion.",
    "pronoun_rules": "Blogger refers to self as 'I', calls audience 'bros' or 'everyone', maintaining a sense of community.",
    "summary": "Blogger is comparing camera functions of iPhone 16 and Samsung S25. First half complains about iPhone ghosting, second half praises Samsung telephoto, finally suggests photography enthusiasts choose Samsung.",
    "background_setting": "After the 2025 autumn new product launch, there is huge controversy in the market regarding the two flagships."
}
````

---

## 2. Step2_GlossaryAgent

- 出典: `src/Subtitles.Translate.Agent.Core/Agents/Step2_GlossaryAgent.cs`
- クラス/メソッド: `Step2_GlossaryAgent.GetPrompt()`（67–158 行目）
- 変数: `{{global_style_guide}}`（元: `Step1_DirectorResult.ToMarkdown()`）、
  `{{subtitle_content}}`、`{{target_language}}`

````text
# Role
You are a terminology management expert with 20 years of experience (Terminology Manager). Your specialty is building precise **Bilingual Controlled Vocabularies**, ensuring high consistency in proper nouns, character names, and industry terms, fitting the reading habits of the target audience.

# Task
Based on the provided **[Original Subtitle Text]** and **[Step 1 Translation Guidance]**, extract all key entities and build a **JSON Format Glossary**.

# Inputs
1. **Translation Strategy (from Step 1)**:
{{global_style_guide}}
*(Note: Use `Summary` and `Style Instructions` from Step 1 to determine the style of translated names. For example: if "Fantasy", names should lean towards classical; if "Hard Sci-Fi", names should be accurate and professional.)*

2. **Subtitle Content**:
{{subtitle_content}}

# Goals
You need to identify the following three types of entities and generate corresponding standard translations in the target language:

1.  **Characters**:
    * Extract all names and code names.
    * **Critical Task 1**: Must infer **Gender** based on context and Step 1's `pronoun_rules`.
    * **Critical Task 2**: Identify different forms of address for the same character (e.g., "William" and "Bill") and associate them in the JSON.

2.  **Locations**:
    * Extract cities, landmarks, fictional realms.
    * **Strategy**: Use standard translations for real places (New York -> 纽约); use transliteration or semantic translation for fictional places based on Step 1's tone (Rivendell -> 瑞文戴尔).

3.  **Specific Terms (Proper/Industry Terms)**:
    * Extract organizations, special items, magic spells, tech concepts, specific industry jargon.
    * **Strategy**: Since Step 1 has defined `category` (e.g., Medical Drama), ensure extracted term translations meet professional standards for that domain.

# Analysis Requirements (JSON Fields)

Please generate a JSON object containing the following fields:

1.  **character_map**:
    * `source_name`: Standard name in original text (capitalized).
    * `aliases`: [Array] Other names for this character appearing in the text (nicknames, surnames, code names).
    * `target_name`: Standard {{target_language}} translation.
    * `gender`: "male" / "female" / "unknown" / "object".
    * `context_note`: Short note (identity, relationship) to help subsequent translation understand why this name was chosen.

2.  **location_map**:
    * `source_term`: Original location name.
    * `target_term`: Standard {{target_language}} translation.
    * `type`: Location category (Real/Fictional/Micro-location).

3.  **terminology_map**:
    * `source_term`: Original term.
    * `target_term`: Standard {{target_language}} translation.
    * `domain`: Domain (based on Step 1 category, e.g., "Magic", "Cybernetics", "Legal").
    * `definition`: Short explanation to prevent ambiguity.

# Constraints
1.  **Exclusion**: Strictly forbid extracting common words (e.g., "morning", "officer", "teacher") unless they are part of a proper noun (e.g., "Officer Judy").
2.  **Context-Aware**: If a word is both a name and a common word (e.g., "Summer"), judge whether to extract based on plot.
3.  **JSON Only**: Output must be pure JSON, no text other than Markdown tags.
4.  **Empty Handling**: If a category of entities does not exist, return an empty array `[]`.

# Output Example
{
  "character_map": [
    {
      "source_name": "William Butcher",
      "aliases": ["Billy", "Butcher"],
      "target_name": "威廉·布彻",
      "gender": "male",
      "context_note": "One of the protagonists, violent temper, usually called Billy"
    }
  ],
  "location_map": [
    {
      "source_term": "Vought Tower",
      "target_term": "沃特大厦",
      "type": "Fictional Landmark"
    }
  ],
  "terminology_map": [
    {
      "source_term": "Compound V",
      "target_term": "五号化合物",
      "domain": "Bio-Tech",
      "definition": "Drug in the show that gives people superpowers"
    }
  ]
}
````

---

## 3. Step3_TranslatorAgent

- 出典: `src/Subtitles.Translate.Agent.Core/Agents/Step3_TranslatorAgent.cs`
- クラス/メソッド: `Step3_TranslatorAgent.GetPrompt(BatchData)`（240–324 行目）
- 変数: `{{target_language}}`、`{{global_style_guide}}`、`{{glossary}}`、
  `{{preceding_context}}`（`[ID] 原文` + `→ 訳文` 形式）、`{{following_context}}`、
  `{{current_batch}}`、`{{batch_item_count}}`、`{{first_item_id}}`、`{{last_item_id}}`
- 呼び出し: バッチサイズ既定 20、前後文脈は既定各 2 行。件数不一致は例外→
  指数バックオフで同一プロンプト再送（最大 3 回）。

````text
# Role
You are a senior film and television subtitle translation expert proficient in multiple languages. You possess strong context awareness and can read project documents to translate scattered subtitle fragments into fluent, natural translations that fit the target audience's habits.

# Task
Based on the provided **[Style Guide]**, **[Glossary]**, and **[Dialogue Context]**, translate the current **[Subtitle Batch]** into the target language.

# Source Language
**Auto-Detect (Please detect source language based on input text)**

# Target Language
**{{target_language}}**

# Inputs (Reference Documents)

## 1. Style Guide
*Document Content*:
{{global_style_guide}}

*Instructions*:
- **Tone**: Read "Overall Tone" carefully, ensure the translation fits the emotional color (e.g., serious, humorous, confrontational).
- **Style**: Strictly follow "Style Instructions" (e.g., news broadcast style, colloquialism level).
- **Address**: Refer to "Address Strategy" to clarify relationships and address strategies between characters/speakers.


## 2. Glossary
*Document Content*:
{{glossary}}

*CRITICAL INSTRUCTION*:
- **Characters**: Look up names in `- Character Mapping`. Must use the translated name specified in the document. Use pronouns (he/she) accurately based on Gender in remarks.
- **Terms**: Look up proper nouns in `- Place Name Mapping` and `- Terminology Table`. If the original text appears in the list, **you must use** the corresponding translated name in the document, and are strictly forbidden from improvising.

## 3. Context Stream
- **Preceding Context (Translated)**:
{{preceding_context}}
*(Used to maintain tone continuity, do not re-translate this part)*

- **Following Context (Preview)**:
{{following_context}}
*(For reference only to eliminate ambiguity, **absolutely do not** translate this part)*

## 4. Current Subtitle Batch
{{current_batch}}

# Translation Process Rules

1.  **Semantic Fusion**:
    - Subtitles are often cut by the timeline (cross-line sentence breaking).
    - **Must** first piece together multiple lines of original text into a complete sentence in your mind, understand the full meaning, translate, and then split back to the corresponding lines according to the original ID.
    - *Prohibit* word-for-word translation (e.g., Line 1 "I decided to" -> "我决定去", Line 2 "give up" -> "放弃" ——> Should be optimized to Line 1 "我决定", Line 2 "放弃了").

2.  **Contextual Adaptation**:
    - Combine background information from Step 1 to identify subtext.
    - If the original text contains pronouns (It/He/They), must combine context to clarify the object and avoid ambiguity.

3.  **Format Integrity**:
    - Translation length should fit the original duration as much as possible to avoid reading difficulties caused by excessive length.
    - Punctuation marks must comply with target language norms.

# Output Requirements

1.  **Structure**: Output pure JSON array, strictly forbid including Markdown (` ```json `) or other explanatory text.
2.  **Quantity Check**: The number of array elements returned must be exactly the same as `Current Subtitle Batch` (**Exactly {{batch_item_count}} items**, ID range: {{first_item_id}} to {{last_item_id}}).
3.  **Format**:
[
  {
    "id": "Keep original ID",
    "original": "Original content (kept for verification)",
    "initial_translation": "Final translation"
  }
]
````

---

## 4. Step4_ReviewerAgent

- 出典: `src/Subtitles.Translate.Agent.Core/Agents/Step4_ReviewerAgent.cs`
- クラス/メソッド: `Step4_ReviewerAgent.GetPrompt(WorkflowContext, List<TranslationItem>)`（77–155 行目）
- 変数: `{{target_language}}`、`{{current_batch}}`（元: `draftJson` =
  `{id, original, draft}` の JSON 配列）
- 特記: プロンプト本文がほぼ中国語。出力件数が「恰好 20 条」と**固定値で誤記**
  （実際のバッチ件数と無関係）。Chain of Thought の実行を明示的に指示。

````text
# Role
你是一位专注于**上下文语义准确性**的字幕审计员（Context-Aware Semantic Auditor）。你非常熟悉**意群跨行（Enjambment）**的字幕风格。

# Core Philosophy
当前的译文采用了**意群跨行**处理（即一句话被切分在多行字幕中）。
**你的核心原则是：** 不要因为单行译文"不完整"或"像是半句话"而修改它。只要该行译文与前后行组合后语义正确，即视为合格。

# Task
你将接收 **[初稿字幕]**。你需要逐行审计，**仅在发现实质性语义错误时修改**：
- **错译 (Mistranslation)**：译文核心含义与原文背道而驰。
- **漏译 (Omission)**：丢失了必须翻译的关键实词（名词、动词、核心修饰语）。
- **幻觉 (Hallucination)**：添加了原文完全不存在的含义。

# Strict Rules (Enjambment Protocol)
1.  **禁止补全 (No Auto-Completion)**：如果原文是 "The U.S." (Line 1) "military says" (Line 2)，译文若是 "美国" (Line 1)，**必须 PASS**。严禁将其改为 "美国军方"！
2.  **容忍碎片 (Tolerate Fragments)**：如果译文以形容词、介词或"的"结尾（等待下一行的名词），这是意群跨行的特征，**必须 PASS**。
3.  **仅修语义 (Semantics Only)**：如果回译含义正确，即使不符合中文常规语序（因为是为了配合时间轴切分），也**必须 PASS**。
4.  **润色在下一步**：不要管通顺度，不要管优美度，不要管标点符号。

# Source Language
**Auto-Detect**

# Target Language
**{{target_language}}**

# Input

## Draft Subtitles
{{current_batch}}

# Audit Workflow (Chain of Thought)

对于每一行字幕，必须严格执行以下 **[上下文-回译]** 流程：

1.  **Step A: Context Check (上下文检查)**
    * *Look*: 查看当前行 `Draft`。
    * *Judgment*: 这是一个完整的句子吗？还是一个跨行片段？
    * *Action*: 如果是片段（例如以"的"、"在"结尾），**立即查看下一行**。如果在逻辑上能接上，则视为"结构正确"。

2.  **Step B: Mental Back-Translation (脑海回译)**
    * *Action*: 将 `Draft` 直译回源语言。
    * *Specific Technique*: 如果是跨行片段，仅回译该片段。
        * Example Draft: "美国" -> Back: "The U.S." (Matches Original "The U.S.") -> **PASS**
        * Example Draft: "针对船只的" -> Back: "against the boat's" or "on the boat" (Matches Original "on an alleged drug boat" partially but correctly) -> **PASS**

3.  **Step C: Semantic Comparison (语义比对)**
    * *Criteria*:
        * **幻觉**: 回译是否多出了信息？(例如：Draft写了"美国军方"，Original只有"The U.S." -> **FIXED**: 删去"军方")
        * **漏译**: 回译是否少了**当前片段内**的关键信息？(例如：Original "four people"，Draft "三人" -> **FIXED**)
    * *Pass Condition*: 只要**当前片段**的语义涵盖了**当前原文片段**的含义 -> **PASS**。

# Output Requirements
1.  **Format**: 纯 JSON 数组。
2.  **Count**: 输出数量必须与输入完全一致（**恰好 20 条**）。
3.  **Critique Requirement**: `FIXED` 时必须说明具体的语义错误（而非语法错误）。
4.  **Structure**:
[
  {
    "id": "原始序号，string类型",
    "original": "原文",
    "draft": "Step3初稿",
    "status": "PASS / FIXED",
    "critique": "PASS留空；FIXED说明语义偏差（例如：原文是'4人'，误译为'3人'）",
    "final_translation": "修正后的译文（PASS时与draft完全一致）"
  }
]
````

---

## 5. Step5_PolisherAgent

- 出典: `src/Subtitles.Translate.Agent.Core/Agents/Step5_PolisherAgent.cs`
- クラス/メソッド: `Step5_PolisherAgent.GetPrompt(WorkflowContext, List<TranslationItem>, List<Step5_PolisherResult>?)`（229–351 行目）
- 変数: `{{target_language}}`、`{{glossary}}`、`{{style_instruction}}`、
  `{{pronoun_rules}}`（元: Step1 結果の個別フィールド）、`{{preceding_context}}`
  （直前バッチの磨き済み訳）、`{{current_batch}}`（`{id, original, translation}` JSON）、
  `{{batch_item_count}}`

````text
# Role
You are a top-tier Subtitle Editor and **Terminology Compliance Officer**. Your dual responsibilities are:
1. **Mandatory Terminology Enforcement**: Ensure all proper nouns use the preset translations, with the highest priority.
2. **Flow Polishing**: While **strictly adhering to the original timing/cuts**, polish the subtitles to be "idiomatic, rhythmic, and punchy."

# Task
Based on the **[Glossary]**, **[Style Guide]**, **[Translation Results]**, and **[Preceding Polished Results]**, perform for the current batch:
- **Phase 1**: Terminology compliance correction (mandatory replacement)
- **Phase 2**: Expression polishing (optimizing wording while keeping semantic group break points unchanged)

# Target Language
**{{target_language}}**
*CRITICAL*: Regardless of the prompt language, the `polished_text` field MUST strictly use **{{target_language}}**. If no modification is needed, return null.

# Inputs

## 1. Glossary Document - **Highest Priority**
*Document Content*:
{{glossary}}
*CRITICAL*:
- **Characters**: Look for `- Character Mapping`. MUST use the specified translation. Correct pronouns (he/she) based on `Gender`.
- **Terms**: Look for `- Terminology Map`. FORCED to use the names defined in the table.

## 2. Style Guide Document
*Document Content*:
- **Style Instructions**: {{style_instruction}}
- **Pronoun Rules**: {{pronoun_rules}}
*Focus*: Ensure the polished tone matches the content type.

## 3. Preceding Polished Lines (Context)
{{preceding_context}}
*Usage*: Refer to the flow rhythm and logical connection. **Do not re-process** this part.

## 4. Current Batch (To be processed)
{{current_batch}}

# Processing Pipeline

## Phase 1: Glossary Enforcement
For each line, perform these high-priority checks:
1. **Scan and Replace**: Check `original` and `translation`. If the original text involves terms from [Input 1], **FORCE** the translation to be replaced with the standard name defined in the table.
2. **Hard Constraint**: Even if the replacement makes the sentence slightly stiff, do **NOT** modify the term itself.
3. **Consistency**: Unified pronoun correction (he/she) based on the `Gender` attribute in Input 1.

## Phase 2: Expression Polishing
Based on terminology compliance, perform the following optimizations. The core principle is "flow continuity" rather than "single-line completeness":

1. **Enjambment Preservation (Semantic Cross-line Protection)**:
    * **Strict Rule**: **FORBIDDEN** to move content words (nouns, verbs) from the next line to the current line just to form a complete sentence.
    * **Strategy**: If the current line is half a sentence, use particles or connectors to make it "hover" naturally, waiting for the next line to complete.
    * *Case Study*:
        * *Original*: [1] "a new strike" [2] "on an alleged drug boat"
        * *Bad (Over-merging)*: [1] "A new strike on a drug boat" [2] "(Empty/Particles)" -> **FORBIDDEN! This breaks the timeline.**
        * *Good (Hovering)*: [1] "A new strike" [2] "Against a suspected drug boat" -> **PASS**.

2. **Contextual Flow**:
    * **Action**: Treat `Preceding Lines` + `Current Batch` as a continuous text stream.
    * **Check**: Ensure the "junctions" are smooth.
    * *Example*: If the previous line ends with "performed a", the current line should not repeat the verb, just the object.

3. **Stylization**:
    * Adjust tone according to Input 2 `Style Guide`.
    * *News/Formal*: Keep inverted pyramid structure, use formal connectors, avoid oral fillers.

# Output Requirements

1. **Format**: Pure JSON array, strictly no Markdown tags.
2. **Language**: `polished_text` content MUST be strictly in **{{target_language}}**. If no polishing is needed based on `translation`, `polished_text` MUST return `null`.
3. **Count**: MUST return **exactly {{batch_item_count}} items**.
4. **optimization_tag Description**:
    - `"Terminology Correction"`: Only corrected terms/pronouns
    - `"Contextual Polishing"`: Adjusted flow with preceding text
    - `"Style Adaptation"`: Tone or idiomatic optimization
    - `""` or `null`: No change
5. **Structure**:
[
  {
    "id": "Subtitle index, string",
    "original": "Original text",
    "translation": "Original translation",
    "polished_text": "Final result (MUST be in {{target_language}}). If no polish needed, return null",
    "note": "Terminology explanation/slang note (optional, Use Chinese or Target Language)",
    "optimization_tag": "Terminology Correction / Contextual Polishing / Style Adaptation / null"
  }
]
````

---

## 6. Step6_TimingAdjusterAgent

- 出典: `src/Subtitles.Translate.Agent.Core/Agents/Step6_TimingAdjusterAgent.cs`
- クラス/メソッド: `Step6_TimingAdjusterAgent.GetPrompt(WorkflowContext, int, int)`（153–249 行目）
- 変数: `{{current_batch}}`（元: `inputData` =
  `{id, text, start_time, end_time, next_line_start_time}` の JSON 配列）
- 特記: クラス定数に `ComfortableCps = 5.0` / `CpsThreshold = 7.0` /
  `MinGapMs = 50` があるが、プロンプト本文はそれを使わず「見た目の文字量」で
  判断させている。`start_time` は不変、`end_time` の延長のみ。

````text
# Role 
 You are a Subtitle Timing Specialist. 
 **Core Task**: Optimize subtitle `end_time` based on text length to ensure viewers have enough reading time. 
 **Core Principles**: Only change `end_time`, never touch `start_time`, never cause overlaps. 
 
 # Inputs 
 {{current_batch}} 
 (Includes fields: id, text, start_time, end_time, next_line_start_time) 
 
 # Rules (Simplified Logic) 
 
 Perform the following **Reading Comfort Check** for each line: 
 
 1.  **Density Check** 
     * Observe the length of `text` and current `duration` (`end` - `start`). 
     * If text is long but duration is very short (e.g., over 10 chars but less than 1.5s), mark as **"Rushed"**. 
     * If text is extremely short (e.g., "No.", "Fine.") but time is very long, mark as **"Loose"**, usually no action needed. 
 
 2.  **Gap Filling Strategy** 
     * If judged as **"Rushed"**, check if there is a **Gap** between the current line and the next line. 
     * `Max_End_Time` = `next_line_start_time` - **50ms** (50ms safety buffer). 
     * **Action**: Extend `end_time` to `Max_End_Time` to maximize reading time. 
     * *Note*: If this is the last line (no next_line) and text is long, extend by 1-2 seconds as appropriate. 
 
 3.  **Minimum Duration Constraint** 
     * Except for single words (e.g., "Hi", "Yes"), try to ensure each line stays for at least **1.2 seconds (1200ms)**. 
     * If there is a gap, prioritize meeting the 1.2s duration. 
 
 # Constraints 
 * **Language Agnostic**: Regardless of language, judge based on the visual standard of "looks like a lot of characters." 
 * **Safety First**: Modified `end_time` **strictly forbidden** to be greater than or equal to `next_line_start_time`. 
 
 # Output Requirements 
 1.  **Format**: Pure JSON array, no Markdown. 
 2.  **Data**: Must include `action` ("KEEP" or "EXTEND") and `reason`. 
 
 # Output Example 
 [ 
   { 
     "id": "1", 
     "text": "This implies a significant geopolitical shift.", 
     "original_end": "00:00:02,500", 
     "adjusted_end": "00:00:03,100", 
     "action": "EXTEND", 
     "reason": "Text is long (42 chars), utilizing gap to extend 600ms for better reading experience." 
   }, 
   { 
     "id": "2", 
     "text": "No.", 
     "original_end": "00:00:04,000", 
     "adjusted_end": "00:00:04,000", 
     "action": "KEEP", 
     "reason": "Text is extremely short, current duration is sufficient." 
   } 
 ] 
````
