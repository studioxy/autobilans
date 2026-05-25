## 2024-05-24 - Optimizing `_is_leaf_account` performance
**Learning:** The method `_is_leaf_account` is currently O(N) where N is the number of all accounts, and it gets called inside a loop over all decisions/accounts, making the leaf account resolution O(N^2). This is a bottleneck for ZOiS with many accounts.
**Action:** Replace `_is_leaf_account` with a pre-computed set of non-leaf accounts. Since `account_no`s represent trees using `-`, we can extract all non-leaf prefix paths into a set (O(N) operation), then check for membership in O(1). This brings the overall complexity down to O(N).
