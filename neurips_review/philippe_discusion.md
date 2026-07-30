Philippe (mentor):

> Honestly, I always get attracted to very simple formulations of problems. That's why I shy away from these complex settings (like SWE Bench, or like web agents alike...) 

> I think there's a very simple formulation to study in your NeurIPS submission that would be fantastic. Take only of the experimental benchmarks from that paper, and find a way to build a simulator for which you vary the level of "entanglement" in the response. It might be a little "artificial" at the extremes (forcing the agent to be very independent, or very tied with the assistance response) but it would simplify the setting drastically because you would only have to rely on a single benchmark 

> and I think you would indeed observe that: (1) dropping the assistant messages only works in "independent communication" setting, which is unrealistic, (2) basic context management that's accumulative suffers from the same problems as no management at all, etc. 

> it's a really nice formulation of the problem you've found, but I think the experimental setting has too many variables

Matthew (me):
> yeah the main effort since submission has been filling out a bigger matrix of experiments across benchmarks/method variants/models and that's basically done, but I do like your approach more. Probably cleaner set up to optimize the method against (which I think is somewhat weak right now...) 

Philippe:
> yeah, you then want to build the method that works under **all simulated user conditions** 
> that's a great framing, I don't think you need benchmark duplicity for this at all 
> 
> like imagine you could have a very simple figure that explains the experiment. For a given task from a given single benchmark, we can simulate different users' "entanglement" to assistant turns, and you could show in each column how much the user is relying/depending on what the assistant has said 

> idk, I'm likely oversimplifying



Me:
> indeed I think there's some inconsistency in what method variants work best right now which is explained by the different aims of the benchmarks so I'll definitely think about how we can get the unified version with the entanglement knob... 

Philippe:
> yeah and idk if "entanglement" is the right word, so feel free to dislike it hehe idk if I've brought this up before, but "[decontextualization](https://aclanthology.org/2021.tacl-1.27/ "https://aclanthology.org/2021.tacl-1.27/")" is relevant here, from Eunsol Choi

> because one solution could be: given a user utterance, rewrite it to decontextualize it, then run it through the system.


Me:
> I think pollution reduction is the overall target but entanglement is the right descriptor for why dropping entire messages isn't optimal (other than efficiency reasons)

Philippe:
> Equivalently in multi-turn: given the state of a conversation so far, summarize it into an entirely new user utterance and start a new conversation with that 

Me:
> right right... only concern there would be distinguishing from the normal compaction approaches but I guess the summarization behaviour is subtly different

Philippe:
> btw, the discussion about "reasoning models" not really being "general-purpose reasoners" reminded me of something I was quite excited about 

> I think there's such a thing as "interactive reasoning" or "multi-turn strategic reasoning" or something like that 

> when we were working on Lost in Conv, mid-way through, reasoning models came out (first O1, then Deepseek-R1) 

> and we were terrified that those reasoning models would actually solve our problem... because theoretically, the model could perform a sort of context reorganization/condensing within its reasoning, and therefore not get lost 

> so when we tested out these models, we were scared to death... the result of course was that reasoning models had even more of a drop in performance than non-reasoning models

> and I always thought that meant that reasoning is not a general-purpose reusable thing. They've trained these models for specific kinds of (useful, but narrow) reasoning, such as logic, code organization planning, math, etc. 

> but not really for interactive, clash resolution across turns, changing of mind, type reasoning, which is very distinct 

> and I always wondered if we could somehow generate in some way synthetic reasoning that would perform this sort of reasoning (which of course, given a full problem formulation is likely nothing too complicated), whether we could train reasoning models specifically for multi-turn, interactive, dynamic reasoning 

> and if those models didn't get lost, it would show how this class of reasoning is distinct from more logic/static/single-turn reasoning is
