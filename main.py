"""CAMPUS_SURVIVE application entry point."""

from login import create_profile, validate_login, load_player
import gui
from game.engine import configure


app = configure(gui_module=gui)


def handle_login(student_id, name):
    """Use Module 1 for profile validation/creation, then open home."""
    if validate_login(student_id):
        player = load_player(student_id)
        if player is None:
            gui.show_message("This profile could not be loaded. Please try again.", "error")
            gui.show_login(handle_login)
            return
        # Keep the registered name canonical. The entered name is not used to
        # overwrite an existing student's saved identity.
        app.player = player
    else:
        player = create_profile(student_id, name)
        if player is None:
            gui.show_message("Profile could not be created. Check the Student ID and data file.", "error")
            gui.show_login(handle_login)
            return
        app.player = player

    app._attach_gui_hooks()
    gui.show_home(app.player, app.handle_home_action)


def main():
    gui.show_login(handle_login)
    gui.run()


if __name__ == "__main__":
    main()
