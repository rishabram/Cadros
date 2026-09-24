"""Tamper-evidence for the verified rule store.

canonical_hash() produces a stable sha256 over the canonical JSON form
(sorted keys, compact separators). The engine stamps every RuleGraph with the
fingerprint of the rules it loaded; tests pin the expected value so any edit
to the rule store — value, quote, status, anything — is caught immediately.
"""
import hashlib
import json


def canonical_hash(obj):
    canonical = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
