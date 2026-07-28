# Master Models intro post

I put 97 coding rules in the system prompt. The model followed 0 of 5.

Stock Qwen3-Coder-30B, running locally. I ran 16 edge-case probes.

Tool mechanics first: malformed calls, stalling on empty files. Two harness guards moved that from 6/9 to 9/9 in one afternoon.

Then I tested my repo's own conventions. Plain prompt: 1/5. So I pasted the full 97-rule style guide into the system prompt.

It got worse: 0/5.

Bigger output budget: still 0/5. The same habits survived explicit bans: `React.FC`, DOM poking, `example.com` emails.

That changed the project for me.

Master Models is my attempt to fine-tune small open models into specialists for my own repo conventions. I already froze 20 eval tasks from real commit history before creating a single training sample.

Local tokens already cost $0. This is not a cost play. It is a quality bet.

Has anyone gotten a small local model to follow house style through prompting alone? Or is training the only door?

#LocalLLM #FineTuning #OpenSourceAI #AIEngineering #BuildInPublic

## First comment

Repo, evals, and the raw probe results:
https://github.com/Rajveerx11/Master-Models
