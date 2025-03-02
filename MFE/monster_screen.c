/**
 * Monster browser screen for Angband
 *
 * This file provides a C interface to the Python-based monster browser.
 */

#include "angband.h"
#include "ui-input.h"
#include "ui-output.h"
#include "ui-term.h"
#include "cmd-core.h"

/**
 * Launch the Python-based monster browser
 */
void do_cmd_monster_browser(void)
{
    char cmd[256];
    
    /* Clear the screen */
    Term_clear();
    
    /* Display a message */
    c_msg_print("Launching monster browser...");
    Term_fresh();
    
    /* Build the command to run the Python script */
    strnfmt(cmd, sizeof(cmd), "python3 %s/src/MFE/show_monsters.py --curses", ANGBAND_DIR_BASE);
    
    /* Save the screen */
    screen_save();
    
    /* Reset the terminal to a normal state for external program */
    Term_xtra(TERM_XTRA_REACT, 0);
    Term_xtra(TERM_XTRA_NORMAL, 1);
    Term_fresh();
    
    /* Run the Python script */
    if (system(cmd) != 0) {
        /* If the curses version fails, try the non-curses version */
        strnfmt(cmd, sizeof(cmd), "python3 %s/src/MFE/show_monsters.py", ANGBAND_DIR_BASE);
        system(cmd);
    }
    
    /* Restore the terminal to Angband's preferred state */
    Term_xtra(TERM_XTRA_REACT, 0);
    Term_xtra(TERM_XTRA_NORMAL, 0);
    Term_fresh();
    
    /* Load the screen */
    screen_load();
    
    /* Refresh */
    Term_fresh();
} 