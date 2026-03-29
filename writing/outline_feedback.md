This is feedback from my mentor on the initial draft/outline. What we're talking about when we say test time scaling is that we're investing more compute at test time to do this kind of self reflection, and even more when you consider the meta-self-reflection that is done via memory learning. This is in contrast to fine-tuning the model itself to solve this problem-- we're using an inference time intervention that scales test time compute. The usual benefit of the opposite, train-time compute is that the improvement is amortized into the model. We absorb some of that benefit with the memory learning thing, but even then we still need to use the reflection step even after memory does its thing.

Anyways please prepare draft2.md from this feedback.

# Message 1

I had a quick pass through, and it's a good first draft. I would frame the work a bit less around "context editing" and more generally about test-time scaling, following Jianfeng's suggestion. Even if the current work is more focused on context editing, we can make it broader by the time of the submission.

RE: the title: "Context Editing" and "History Rewriting" kind of say the same thing, and I would use neither in light of my previous comment. I would include "context rot/pollution/etc" to make it clearer what we are addressing. To sound a bit academic, what about "Context Contamination" instead of "Rot"?

Maybe some version:

- Test-Time Scaling for Overcoming Context Contamination in Multi-Turn Conversations
- Overcoming Context Contamination in Multi-Turn conversation with Test-Time Scaling

I think we can explore better titles, but generally I would include "test-time scaling", "Multi-turn Conversations", and "Context Contamination/pollution" to overcome/mitigate/reduce/address/defeat. 
# Message 2
A few more comments that are related:

(1) "test-time scaling" is broad but also bland as there's plenty of work in that space. At the risk of making the title too long, what about adding something more specific yet still punchy such as "executive function"? To me, "test-time scaling" and "executive function" are related, but the latter has more of human (or human-AI) element. 

(2) Some of your methods such as "Agentic Edit" and "reflect-and-unify" are instantiations of what we discussed with Nebojsa (at least loosely). So, between sections 3.1 and 3.2, you could add a highlight the behavior you'd like to infuse into the assistant, and could almost reuse what Nebojsa wrote/said about executive function, and then later (context strategies, etc) explain how your specific methods relate to executive function. 

(3) The intro lacks a punch sentence/pargraph after you overview the challenges (4-5 paragraphs on challenges and limitations might be a bit too long btw). After you are done with challenges, you could start a new paragraph with "To address these challenges, we introduce a framework of methods centered on the idea of executive function [...]. I see that you have methods listed under "Contributions", but that reads more like a summary of contributions. It would be more effective to include your contributions as part of the narrative of your intro.

You might want to share the doc with Nebojsa as well. In light of that, I suggest you let us comment but not edit the doc

# Message 3

I would first introduce executive function as something that psychologists know how to address when humans face similar problems (distracting context, etc). Now, we're talking about executive function in an HAI setup, which might bring even more validity to focusing on executive function, but admittedly that's a bit gratuitous. The connection between HAI and executive function could be just mentioning that the later is implemented in an HAI task setup.
