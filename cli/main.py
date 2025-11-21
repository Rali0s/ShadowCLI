"""Command line entry point for ShadowOps offline toolkit."""

from __future__ import annotations

from .navigation import ENTRIES


def run_all() -> None:
    for entry in ENTRIES:
        print(f"\n=== {entry.label.upper()} ===\n")
        entry.handler()


def _fallback_main() -> None:
    """Original simple-term-menu based main entry used as a fallback."""
    try:
        from .menu import Menu, MenuItem
    except Exception:
        # If the thin menu helper isn't importable, run all modules directly
        run_all()
        return

    actions = [MenuItem(entry.label, entry.handler) for entry in ENTRIES]
    actions.insert(0, MenuItem("Run all modules", run_all))
    menu = Menu("ShadowOps Offline Toolkit", actions)
    menu.show()


def main() -> None:
    """Primary entry point. Prefer Cement-powered persistent shell (Rich-based) when available.

    Falls back to the original simple-term-menu interactive menu if Cement isn't available.
    """
    import sys

    try:
        # Prefer the Cement + Rich persistent shell as the parent menu
        from .cement_app import main as cement_main
    except Exception as exc:
        # If Cement (or its imports) are unavailable, fall back to the simple menu.
        # Print a short diagnostic so users understand why the rich shell wasn't used.
        import traceback

        print("[info] Cement-based shell unavailable, falling back to simple menu.")
        print("[info] Reason:")
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stdout)

        # If the caller provided argv (e.g. 'default' or module selector) try to
        # honor it with the fallback menu; otherwise show the interactive menu.
        args = sys.argv[1:]
        if args:
            # support 'default' as the normal Cement default command
            if args[0] == "default":
                _fallback_main()
                return
            # if a numeric module selection or known keyword was passed, try to
            # start the fallback menu and dispatch accordingly
            try:
                from .menu import Menu, MenuItem

                # emulate selection if possible
                sel = args[0]
                menu = Menu("ShadowOps Offline Toolkit", [MenuItem(entry.label, entry.handler) for entry in ENTRIES])
                # attempt to resolve and run selection; fall back to interactive
                try:
                    idx = int(sel)
                    if 1 <= idx <= len(menu.items):
                        menu.items[idx - 1].handler()
                        return
                except Exception:
                    pass

            except Exception:
                # nothing more we can do; fall through to interactive fallback
                pass

        _fallback_main()
        return

    # Delegate to the Cement entrypoint (it handles KeyboardInterrupt cleanly).
    # Forward any CLI args provided to this module to the Cement app so
    # commands like `python3 -m cli.main default` are honored.
    cement_main(argv=sys.argv[1:])


if __name__ == "__main__":  # pragma: no cover
    main()
