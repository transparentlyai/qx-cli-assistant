Task: Output a Markdown document that summarizes the **entire interactive coding session that occurred *before* this current summarization request**. This summary is for hand-over to another AI that already possesses full project and environment context.

**Important Scope Note:** Focus *exclusively* on the conversation, actions, and developments from the session *prior to receiving this summarization instruction*. Do **not** include any information about the task of creating this summary itself.

The output document must include the following sections, detailing the historical conversation and actions:

**1. Core Session Objective & User Intent:**
    * Primary goal statement for the overall session.
    * Original user requests that initiated or guided the work.
    * Key clarifications and scope definitions (including agreed scope changes/constraints throughout the session).
    * Desired end-state description for the tasks and actions performed so far (what success looked like for those prior activities).

**2. Session Status, Action Log, and Resumption Plan:**
    * **A. Action Log:** For each significant action or task undertaken during the prior session:
        * Action description (e.g., "Implemented user authentication module," "Attempted to debug X issue").
        * Status (e.g., Completed, Partially Completed, Pending User Feedback, In-Progress, Failed, Aborted).
        * Key outcomes or partial results summary (even if incomplete, note what was achieved or learned).
        * Specific next steps for *this individual action* if it's not fully complete (e.g., "Requires refactoring of function Y," "Awaiting API key from user").
    * **B. Consolidated Resumption Plan & Next Steps:** This section outlines how to pick up the work.
        * **Overall Session Status:** Briefly state the overall status of the session's objectives (e.g., "Main objective X is 70% complete," "Blocked on Y," "Ready for next phase").
        * **Immediate Next Action(s) Recommended:** Clearly list the 1-3 highest priority actions the next AI should take to resume progress effectively. Be specific.
        * **Pending Actions/Open Loops:** List any other tasks that were started but not completed, or user requests that are still pending.
        * **Information Needed for Resumption:** Specify if any critical information, decisions, or resources are immediately required to unblock or continue the work (e.g., "User decision on option A vs. B," "Access to database Z").
        * **Suggested Starting Point:** If applicable, suggest a specific file, function, or point in the workflow for the next AI to begin its work.

**3. File-System & Workspace Snapshot (Reflecting state *before* this summary request):**
    * **File Operations Log:** A chronological or grouped list of file modifications.
        * Operation type (e.g., created, modified, deleted, renamed).
        * Full file path.
        * Brief summary of changes made to the file (e.g., "added function X," "fixed typo," "refactored Y section").
    * **Temporary Files or State Summary:**
        * List of any temporary files created (paths and purpose).
        * Summary of any significant in-memory state that isn't captured in files but would be needed to resume (e.g., "active database connection configured for X").
        * Indicate if temporary files/state are essential for resumption or if they can/should be cleaned up.

**4. Code, Execution & Error Summaries (From the prior session):**
    * **Significant Code Snippets References:**
        * Reference key code snippets that are crucial for understanding the work done or for resuming (e.g., provide file path and line numbers, function names, or a unique identifier if used). Do not include full code snippets unless extremely short and critical.
    * **Command Execution Summaries:**
        * Log of important commands executed (e.g., compilation steps, script executions, tool commands).
        * Indicate success/failure.
        * Include very brief, key output if it directly influenced subsequent actions or understanding (e.g., a specific error message that was then addressed).

**5. Environment (As relevant to the prior session):**
    * Summary of environment aspects that were relevant or problematic during the session (e.g., "Python version conflict resolved," "Specific API endpoint X was unavailable," "Used Docker container Y"). Avoid generic environment listings; focus on what impacted the session.

**6. Session Reasoning & Strategy (Reflecting the thinking *during* the prior session):**
    * **Problem Solving:** Summary of key problems encountered.
    * **Solutions & Approaches:** Summary of solutions implemented or attempted, and the overall strategy taken.
    * **Alternatives Considered:** Brief mention of alternative approaches that were discussed or considered but not pursued.
    * **Key Design Decisions Log:** Important design choices made and their rationale.
    * **Open Questions & Ambiguities:** Any unresolved questions or ambiguities that arose during the session and might need future attention.
    * **Known Limitations & Tradeoffs Accepted:** Any limitations identified or tradeoffs made.

**7. User Context & Preferences (Observed *during* the prior session, excluding initial system instructions to *this* AI):**
    * **Tracked User Variables Data Summary:** If any specific user data points were explicitly tracked or utilized.
    * **User-Stated Preferences/Constraints:** Explicit preferences or constraints voiced by the user during the interaction.
    * **Implicit User Patterns Observed:** Any recurring patterns in user requests, feedback, or coding style if clearly discernible and relevant.

**Output Format Guidance:**
* Use Markdown for structuring the document.
* Be concise: focus on information essential for context and resumption. Avoid verbose descriptions or full file dumps.
* Ensure all information pertains *only* to the conversation and actions *before* this summarization task was initiated.
