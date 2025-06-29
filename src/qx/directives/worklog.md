### Worklog Maintenance & Context Restoration

#### 1. Mandate, Purpose, & Session Initialization
You must maintain a clear and concise project worklog stored in the file `.Q/worklog.md`.
First, check if the file exists:
If worklog.md does exist, read it and continue. 
If worlog.md does not exist, ask the user if you should create it. If the user agrees, create the file and write the first entry.

This log is essential for tracking your progress and decisions throughout the project.
The purpose of this log is to help you or another Agent quickly understand the project's context and resume tasks efficiently. 
Consistent and accurate maintenance of this log is mandatory for effective long-term project engagement.

---

#### 2. When to Add a New Log Entry
You should append a new, timestamped entry to `.Q/worklog.md` in the following situations:

* After Significant Actions: Following any major coding work (like creating, modifying, or fixing code) or important configuration changes.
* Before Complex Tasks: Before you start generating large blocks of code or planning a multi-step task, log your intended approach.
* On Key Decisions: When you finalize important choices about the project's architecture, algorithms, or the libraries you'll use.
* When Identifying Roadblocks: Whenever you encounter new challenges, critical issues, or have questions that block your progress.
* At the End of a Session: Before you stop work for a break or at the conclusion of an interaction.

---

#### 3. Log Entry Guidelines
Each new log entry should start with a timestamp and be separated from the previous entry by a horizontal rule (`---`). Your log entries should be:

* Descriptive and Clear: Write in natural language. The goal is to clearly explain what you did, what you're working on, and what's next. Focus on being easily understandable.
* Concise: While being descriptive, keep your entries brief and to the point. Avoid unnecessary detail. Focus on the information that is critical for resuming work.
* Organized: Structure your entries logically. A good practice is to briefly cover:
    * What was just done: A summary of your last significant action.
    * What's next: The immediate next steps you plan to take.
    * Key information: Any critical decisions, issues, or new reference links.

---

#### 4. What to Include in Your Log Entries
Focus on logging information that isn't immediately obvious from looking at the code. Good things to include are:

* The high-level objective you are currently working towards.
* Files or specific functions/classes that were the focus of your last session.
* Key decisions you made and a brief reason for them (e.g., "Switched to the Argon2id hashing algorithm for better security").
* Any issues, roadblocks, or open questions that need to be addressed.
* Your planned next steps, noting their priority if applicable.
* Critical links to documentation or other resources you used.

Do not include large snippets of code. Instead, refer to code by its file path and the name of the function or class.

---

#### 5. Initial Log Entry
If the `.Q/worklog.md` file does not exist, you must create it. The very first entry should record the current timestamp, the main goal of the project, and the first action you plan to take.
you must keep all the log entrries in chronological order, with the most recent entry at the bottom of the file.
