# AI Coding Assistant – Concise Session-Handover Prompt

**Task:** Output **one** JSON object summarising this session for hand-over to another AI that already has full project and environment context.
Focus on objectives, key actions/decisions, code- and file-changes. Skip full file contents, detailed environment data, and most timestamps.
Embed a `handover_instructions` object (see § IX).

---

## I  Core Session Objective & User Intent

1. `Primary_Goal_Statement` – main goal.
2. `Original_User_Requests` – array of initial prompts.
3. `Key_Clarifications_Scope_Definitions` – agreed scope changes/constraints.
4. `Desired_End_State_Description` – what success looks like.

---

## II  Interaction & Action Log

### 1 `Summarized_Dialogue` (array, per turn)

* `turn_type`: `"user_input"` | `"ai_response"`
* `core_intent_summary`
* `extracted_data_parameters` (obj, opt)
* `decision_commitment_flags` (array, opt)

### 2 `Detailed_Action_Record` (array)

* `action_id`, `action_type`, `description`
* `inputs_parameters` (obj, opt)
* `outcome`: `{status, details}`
* `generated_artifacts_references` (array, opt)
* `rationale_dialogue_link` (str, opt)

### 3 `Pending_In_Progress_Actions` (array)

* `action_description`, `next_steps` (array), `partial_results_summary_or_ref` (str)

---

## III  File-System & Workspace Snapshot

1. `File_Operations_Log` (array) – `{operation_type, file_path, destination_path(opt), change_summary}`
2. `Current_Codebase_Snapshot_Summary` (map) –
   `file_path` ➜ `{status, brief_description_of_last_change_or_purpose}`
3. `Workspace_Context_Summary` – `{current_working_directory, key_session_variables_or_state(opt)}`
4. `Temporary_Files_Or_State_Summary` (array, opt) – `{type, identifier_name, location_or_reference, purpose}`

---

## IV  Code, Execution & Error Summaries

1. `Significant_Code_Snippets_References` (array, opt) – `{snippet_id, language, purpose_description, code_excerpt_or_reference, context_reference_id(opt)}`
2. `Command_Execution_Summaries` (array, opt) – `{command_string_summary, working_directory, output_summary, exit_code(opt)}`
3. `Error_Log_Summaries` (array, opt) – `{error_id, source_of_error_summary, error_message_summary, stack_trace_summary(opt), current_status}`

---

## V  Environment & Dependencies

*(Omitted – receiving agent already has this context.)*

---

## VI  AI Internal Reasoning & Strategy

* `Problem_Decomposition` (array) – `{sub_task_id, description, status}`
* `Current_Solution_Approach_And_Strategy` – `{overall_strategy_description, next_strategic_steps}`
* `Alternative_Approaches_Considered` (array, opt)
* `Key_Design_Decisions_Log` (array)
* `Open_Questions_And_Ambiguities` (array, opt)
* `Known_Limitations_And_Tradeoffs_Accepted` (array, opt)
* `Agent_Confidence_Assessment` (obj, opt)

---

## VII  User Context & Preferences

* `Tracked_User_Variables_Data_Summary` (obj, opt)
* `User_Stated_Preferences_Constraints` (array, opt)
* `Implicit_User_Patterns_Observed` (array, opt)

---

## VIII  Session Metadata

* `AI_Assistant_Model_And_Version`
* `Originating_Session_Identifier` (opt)
* `Generating_Agent_Instance_ID` (opt)
* `Archive_Creation_Timestamp` (ISO 8601)

---

## IX  `handover_instructions` (embedded JSON object)

```json
{
  "purpose": "Concise session summary for AI hand-over.",
  "format_overview": "Single JSON object with clearly named section keys.",
  "recommended_resumption_strategy": [
    "1. Review I & VI for goals and current plan.",
    "2. Check III and II.Pending_In_Progress_Actions; re-read modified files.",
    "3. Inspect IV for recent code, commands, and errors.",
    "4. Use VI for previous reasoning and open issues.",
    "5. Consider VII for user preferences.",
    "6. Clarify ambiguities before major changes."
  ],
  "interpreting_data_notes": {
    "dialogue_summaries": "See II.Summarized_Dialogue for intents/decisions.",
    "action_logs": "Correlate II.Detailed_Action_Record with III snapshots.",
    "error_handling": "Resolve items in IV.Error_Log_Summaries.",
    "file_content_omitted": "Re-read actual workspace files as needed."
  },
  "safety_guidelines_for_resumption": [
    "Verify workspace state before acting.",
    "Ask for clarification on unclear points.",
    "Validate critical info against workspace."
  ],
  "contact_for_issues_with_context_format": "N/A"
}
```

