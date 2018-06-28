Petriish
========

Structural workflow engine for running cascades of processes. Inspired by structural Petri workflow nets (hierarchical workflow nets?).

Advantages
 * Unix philosophy compliant: it does one thing well and it's easily integrated with other programs.
 * Workflow description reflects workflow structure. No unstructured, ugly DAGs ;) Only a pretty, pure tree.

Structural workflow description
-------------------------------

Workflow is a tree. It has some advantages over DAG of tasks, but not every DAG can be converted to structural workflow. Also, some structural workflows cannot be expressed as DAG.

Structural workflow make it easy to construct workflow on different levels of abstraction, and allows for precise tracing of error and determining nodes it can affect. (Verbose tracing is not implemented yet.)

Upon execution workflow (after some, potentially indefinite, time spent *running*) may *suceed* or *fail*.

Workflow tree has following type of nodes:

 * **sequence**

   Sequentially execute many *sub-workflows*, one after another. Failure in any *sub-workflow* results in whole sequence failure. Sequence of length zero succeedes immediately.

 * **alternative**

   Execute excatly one of many *sub-workflows*. To ensure deterministic behaviour one *sub-workflow* must suceed and all others must fail. If this is not the case while alternative fails. Alternative of length zero fails immediately.

 * **parallelization**

   Execute many *sub-workflows* in parallel. For parallelization to succeed all *sub-workflows* must succeed. Parallelization of length zero suceeds immediately.

 * **repetition**

   Execute sub-workflow (*body workflow*) zero or more times. To ensure determinism this node has also *exit workflow*. Both sub-workflows gets executed. Exactly one of them must succeed. If *exit workflow* suceeds repetetion suceeds. If *body workflow* suceeds repetition keeps recuring. If both workflows suceed or both fail then repetition fails.

 * **leaf task**

   One, atomic (non-splittable) action. In case of petriish it's a call for command. Exit code 0 means sucess and anything else is failure.

Example
-------

Check out `example.py`
