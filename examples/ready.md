# Portable archive reader migration (synthetic)

Replace the archive reader's byte-order-dependent implementation with a portable
reader across all 40 modules, the streaming layer, command-line integration and
compatibility tests. This is a substantial cohesive migration, potentially thousands
of changed lines. The single governing intent is byte-for-byte compatible archive
reading on both supported endian architectures.

The owner has frozen these requirements: preserve the public API, all format v1/v2
archives, error codes, streaming memory bounds and existing CLI output. No format
redesign or new user-facing behavior. The implementer is authorized to update the
reader and its tests. Both architecture runners and signed reference archives are
available in the implementation environment. No external approval is outstanding.

Acceptance: both runners pass the same golden archive corpus; public API and CLI
compatibility tests pass; corrupt-input error codes match; the streaming test stays
under the existing 32 MiB bound. An independent reviewer gives one verdict on portable
compatibility. Locate reusable endian helpers and derive internal buffering changes
through normal engineering research. Keep this work together: helpers, streaming and
CLI integration jointly establish the same compatibility guarantee.
