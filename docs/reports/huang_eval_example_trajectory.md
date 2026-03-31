# WildChat Example: Context Curation Outperforms Both Baselines

This document presents a representative example from the Huang et al. reproduction evaluation where our context curation method (S2) produces a substantially better response than both the full-context (FC) and assistant-omitted (AO) baselines.

## Conversation Overview

**Source:** WildChat-1M, conversation `300289e3c40bce0727e7...`  
**Topic:** Iterative debugging of a Maven/Java build in GitHub Codespaces  
**Rounds:** 8 user-assistant exchanges  
**Original model:** gpt-3.5-turbo-0301  

The user is trying to run `mvn clean install` in GitHub Codespaces and encounters a sequence of build errors. The conversation is highly stateful: each user message references specific error output and prior assistant suggestions, making it a clear case where blanket assistant-message omission (AO) loses critical context.

## Conversation History (Abbreviated)

**Turn 0 [User]:** Shares a GitHub repository link.

**Turn 1 [Assistant]:** Generic explanation of what GitHub is (not useful -- model can't access the repo).

**Turn 2 [User]:** "Why do I keep getting error when running mvn clean install in GitHub Codespaces?" Pastes a Maven build error: `No compiler is provided in this environment. Perhaps you are running on a JRE rather than a JDK?`

**Turn 3 [Assistant]:** Correctly identifies the JRE vs JDK issue. Suggests checking `java -version` and installing a JDK.

**Turn 4 [User]:** "I am using Codespaces" (short follow-up referencing the environment established earlier).

**Turn 5 [Assistant]:** Provides Codespaces-specific instructions: `sudo apt-get install -y default-jdk`, set `JAVA_HOME`, add to `.bashrc`.

**Turn 6 [User]:** "Now I get:" -- pastes a NEW error: `Fatal error compiling: error: invalid target release: 17`

**Turn 7 [Assistant]:** Suggests updating `pom.xml` to set Java 17 as source/target.

**Turn 8 [User]:** "Still getting" -- pastes the SAME error again after trying the fix: `Fatal error compiling: error: invalid target release: 17`

This is the turn we examine. The user is saying "still getting [the same error]" after following the assistant's previous suggestion. This is a classic **no_feedback** turn: the user references the prior assistant response implicitly ("still getting" implies "I tried your fix and it didn't work") without providing explicit corrective feedback.

## Turn 8: Three Conditions Compared

### AO Response (Assistant-Omitted)

AO replaces all prior assistant messages with `[Response provided]` placeholders. The model sees the user's error messages but has no record of what was already suggested and tried.

> That error means the Java compiler Maven is using does not understand "target release 17" -- in other words Maven is running with a javac older than Java 17 (or no javac at all). This often happens in Codespaces when the JDK is missing or JAVA_HOME / PATH points to a JRE or different Java than the one you checked with java -version.
>
> Do these steps to diagnose and fix:
>
> 1) Check what Maven and the toolchain actually see  
> Run: `java -version`, `javac -version`, `mvn -v`
>
> 2) If javac is missing or older than 17, install a JDK  
> `sudo apt-get update && sudo apt-get install -y openjdk-17-jdk`
>
> 3) Make sure alternatives and JAVA_[*truncated*]

**Problem:** AO's response re-suggests `apt-get install` and checking `java -version`, which the user has already done in prior turns. Without seeing the prior assistant messages, AO cannot know what was already tried and starts from scratch. The user said "still getting" -- implying the previous fix didn't work -- but AO has no record of what that fix was.

### FC Response (Full Context)

FC sees the entire conversation history, including all prior assistant responses.

> The error "invalid target release: 17" means the Java compiler (javac) that Maven is actually running is older than Java 17 or otherwise not compatible with target 17. In Codespaces you need to make sure a JDK 17+ is installed and that Maven is using it.
>
> Quick checklist + commands to fix it:
>
> 1) Check which Java and javac Maven is using: `java -version`, `javac -version`, `mvn -version`
>
> 2) Install OpenJDK 17: `sudo apt-get update && sudo apt-get install -y openjdk-17-jdk`
>
> 3) Point system java/javac to the JDK 17 and set JAVA_HOME:  
> `sudo update-alternatives --install /usr/bin/java java /usr/lib/jvm/java-17-openjdk-amd64/bin/java 1`  
> `sudo update-alternatives --config java  # choose the java-17 entry`

**Problem:** FC is slightly better than AO (it includes `update-alternatives` commands), but it still partially repeats earlier suggestions. The model can see the prior conversation but is anchoring on the same diagnostic approach rather than recognizing that the user already tried the basic install and it didn't resolve the issue.

### S2 Response (Context Curation with v11 Analyzer)

S2 runs the v11 analyzer, which identifies issues in the prior conversation (incorrect diagnostic guidance, missing verification steps) and rewrites the context before generating.

**Analyzer output (abbreviated):**

*Issues identified:*
> The assistant said that seeing "OpenJDK Runtime Environment" in `java -version` means the system has a JRE rather than a JDK. That is not reliable: `java -version` output often contains "Runtime Environment" even when a JDK is installed. The correct, reliable checks are presence and versions of `javac` and the values of `JAVA_HOME`/path to the JDK.

*Aligned (preserved):*
> Maven's "No compiler is provided" message means Maven cannot find `javac` and needs a JDK. Installing a JDK inside Codespaces is a valid remediation path.

**S2's response:**

> Thanks -- the new error ("invalid target release: 17") makes the root cause and the fix straightforward. Below I give a concise diagnosis and exact, copy/paste-ready commands and file edits you can use inside GitHub Codespaces so `mvn clean install` completes successfully.
>
> **1) Root-cause diagnosis (short)**
> - "No compiler is provided" means Maven couldn't find `javac`. `java -version` only shows the runtime, not whether a JDK with `javac` is available to Maven.
> - "invalid target release: 17" means the Java compiler Maven is invoking does not support target/release 17 (either `javac` is missing, it's an older JDK < 17, or Maven is using a JRE-only installation). Even though `java -version` reported OpenJDK 20 earlier, Maven may be picking up a different Java binary via PATH/JAVA_HOME/alternatives. We must ensure a JDK >= 17 is installed and that Maven uses that JDK.
>
> **2) Exact diagnostic and fix steps** [*continues with comprehensive, non-redundant instructions including `update-alternatives`, `JAVA_HOME` exports, `pom.xml` changes with `<release>17`, devcontainer recommendations, and verification steps*]

**Why S2 wins:** The analyzer identified that the prior assistant's diagnostic reasoning was flawed (relying on `java -version` text parsing rather than checking `javac` directly) and that the conversation was stuck in a loop of repeating the same insufficient fix. By rewriting the context to preserve the correct diagnosis (Maven needs a JDK) while removing the flawed reasoning, S2 produced a response that:
1. Correctly diagnoses why the error persists (Maven may be using a different Java than what `java -version` reports)
2. Provides comprehensive, non-redundant steps (doesn't re-suggest things already tried)
3. Includes additional solutions FC and AO both missed (devcontainer configuration, `<release>` tag in pom.xml)

## Judge Evaluations

**FC vs AO (Phase 1):** FC wins on quality.
> "Both responses correctly diagnose the problem. Response A [FC] is slightly clearer and more prescriptive: it provides an explicit checklist, concrete update-alternatives install commands with exact paths, verification steps, and a practical alternative."

**AO vs S2 (Phase 2):** S2 wins on quality.
> "Response B [S2] is substantially more complete and actionable. It provides clear diagnosis, exact diagnostic commands, copy/paste-ready installation and update-alternatives commands, instructions to set JAVA_HOME and PATH, safe pom.xml edits (including use of `<release>17`), devcontainer recommendations for Codespaces, verification steps, and troubleshooting tips."

**FC vs S2 (Phase 2):** S2 wins on quality.
> "Response B [S2] is significantly more complete and actionable. It gives a correct short diagnosis, precise diagnostic commands to run, exact installation and update-alternatives commands, environment variable exports, pom.xml changes, devcontainer recommendations for Codespaces, verification steps, troubleshooting tips, and a short checklist."

## Why This Example Matters

This conversation illustrates the core limitation of AO that Huang et al. identify: on **no_feedback** turns where the user implicitly references prior assistant output ("still getting [the error]"), removing all assistant messages removes essential context about what was already tried.

But it also shows why FC is insufficient: even with full context, the model anchors on its prior flawed reasoning and repeats variations of the same approach. The context is polluted by the earlier incorrect diagnostic ("check `java -version`") and the model cannot break free of that framing.

Context curation (S2) addresses both problems: the analyzer identifies the flawed reasoning, the context rewrite removes it, and the fresh generation produces a more comprehensive response that breaks out of the stuck loop.

## Conversation-Level Summary

Across all 7 evaluated turns in this conversation:

| Turn | User message (abbreviated) | FC vs AO | S2 vs AO | S2 vs FC | S2 edited? |
|------|---------------------------|----------|----------|----------|------------|
| 2 | "Why do I keep getting error..." | AO wins | S2 wins | S2 wins | Yes |
| 4 | "I am using Codespaces" | FC wins | S2 wins | S2 wins | Yes |
| 6 | "Now I get: [new error]" | FC wins | S2 wins | S2 wins | Yes |
| 8 | "Still getting [same error]" | FC wins | S2 wins | S2 wins | Yes |
| 10 | "I do not have a bashrc file" | AO wins | S2 wins | S2 wins | Yes |
| 12 | [Shares GitHub Actions YAML] | AO wins | S2 wins | S2 wins | Yes |
| 14 | "No WAR file generated" + pom.xml | AO wins | S2 wins | S2 wins | No |

S2 wins every turn against both baselines. On turns 4, 6, and 8, the user's messages are highly context-dependent ("I am using Codespaces", "now I get", "still getting"), and AO fails because it cannot connect these to prior discussion. On turns 2, 10, 12, and 14, AO wins over FC (context pollution hurts more than context loss), but S2 still wins because it removes the pollution while preserving useful context.
