# 🎓 The Self-Learning Feedback Loop

One of NulkaAgent's most powerful features is its ability to *permanently learn from its mistakes*.

## How it works

When you submit a query, and the responding agent provides an incomplete or factually incorrect response, you can immediately type:
```bash
/teach
```

This interrupts standard execution and triggers the **Feedback Loop**:
1. The **Teacher Agent** receives your previous query.
2. It bypasses the local models entirely and directly queries the **Universal Oracle** via the command line to fetch the absolute truth.
3. The CLI halts and presents you with a stylized interactive prompt, proposing a new "Lesson Learned" rule based on the Oracle's answer.
4. You can choose to Accept, Reject, or augment the rule by typing a custom response.

## Persistent Memory
Once approved, the rule is structurally appended to the bottom of the failing agent's Markdown backstory file under a `### 🎓 Learned Rules & Guidelines` header.

Because NulkaAgent dynamically loads these files at runtime, the agent permanently retains this knowledge and will apply it to all future sessions automatically!
