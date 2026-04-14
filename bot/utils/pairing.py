from __future__ import annotations

import random


def build_random_pairs(user_ids: list[int]) -> tuple[list[tuple[int, int]], list[int]]:
    """Формирует случайные пары 1:1 и список участников без пары."""
    users = list(dict.fromkeys(int(uid) for uid in user_ids))
    random.shuffle(users)

    pairs: list[tuple[int, int]] = []
    leftovers: list[int] = []

    for idx in range(0, len(users), 2):
        chunk = users[idx : idx + 2]
        if len(chunk) == 2:
            pairs.append((chunk[0], chunk[1]))
        else:
            leftovers.append(chunk[0])

    return pairs, leftovers
