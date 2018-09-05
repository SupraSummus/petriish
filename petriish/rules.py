def rules_to_petrrish(rules, prerequisites, atoms, target):
    """
    Rules are dict target name -> list of methods to build this target.
    Prerequisites are dict method name -> list of prerequisites (target names).
    Atoms is dict method name -> petriish worklofw.
    """

    return petriish.Alternative([
        petriish.Sequence([
            petriish.Parallelization([
                rules_to_petrrish(rules, prerequisites, atoms, prerequisite)
                for prerequisite in prerequisites[method]
            ]),
            atoms[method],
        ])
        for method in rules[target]
    ])
