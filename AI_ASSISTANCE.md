# AI-assisted development disclosure

AI assistance was used to help draft, review, and organize portions of the source code, documentation, tests, and project structure. The candidate must review and understand the submitted code, run the application locally, verify every claimed feature, and disclose this assistance in accordance with the employer's instructions. No claim is made that AI assistance was absent.

The extraction prompt used by the optional local LLM adapter is stored at `prompts/invoice_extraction.txt`. The implementation currently constructs an equivalent prompt in `app/extractor.py`; keep the two synchronized when changing the prompt.
