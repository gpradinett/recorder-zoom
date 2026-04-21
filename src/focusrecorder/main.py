from .presentation.ctk.studio_window import FocusApp


def run():
    app = FocusApp()
    app.mainloop()


if __name__ == "__main__":  # pragma: no cover
    run()
