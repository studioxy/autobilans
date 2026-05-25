## 2024-05-24 - CLI menu exit graceful handling
**Learning:** Pure terminal apps without web frontends still need UX. Users commonly hit Ctrl+C or Ctrl+D in terminal menus when they want to quit, and seeing Python tracebacks (EOFError or KeyboardInterrupt) feels jarring and unprofessional. Gracefully handling these signals to cleanly exit makes the CLI feel much more robust and user-friendly.
**Action:** Always wrap standard `input()` calls in CLI loops with `try/except (EOFError, KeyboardInterrupt)` to catch terminal break signals and provide a clean exit path.
