import micropython
from machine import Pin
import time


class Keypad_Timer () :
    """
    Class to scan a Keypad matrix (e.g. 16-keys as 4x4 matrix) and report
    last key press.
    """

    #! Key states
    KEY_UP      = const( 0 )
    KEY_DOWN    = const( 1 )

    #-------------------------------------------------------------------------

    def __init__ ( self ) :
        self.init()

    #-------------------------------------------------------------------------

    def init ( self ) :
        """Initialise/Reinitialise the instance."""

        keys = [
                'L', 'E', 'R',
                'C', ' ', 'K', 
                '1', '2', '3',
                '4', '5', '6',
                '7', '8', '9', 
                '*', '0', '#',
               ]

        #! Initialise all keys to the UP state.
        self.keys = [ { 'char' : key, 'state' : self.KEY_UP } for key in keys ]

        #! Pin names for rows and columns.
        self.rows = [ 22, 21, 30, 14, 13, 12 ]
        self.cols = [ 25, 24, 23 ]

        #! Initialise row pins as outputs.
        self.row_pins = [ Pin(pin_name, mode=Pin.OUT) for pin_name in self.rows ]

        #! Initialise column pins as inputs.
        self.col_pins = [ Pin(pin_name, mode=Pin.IN, pull=Pin.PULL_DOWN) for pin_name in self.cols ]

        # self.timer = Timer( 5, freq=100 )
        # self.timer.callback( None )

        self.scan_row = 0
        self.key_code = None
        self.key_char = None

    #-------------------------------------------------------------------------

    def get_key ( self ) :
        """Get last key pressed."""

        key_char = self.key_char

        self.key_code = None    #! consume last key pressed
        self.key_char = None    #! consume last key pressed

        return key_char

    #-------------------------------------------------------------------------

    def key_process ( self, key_code, col_pin ) :
        """Process a key press or release."""

        key_event = None

        if col_pin.value() :
            if self.keys[ key_code ][ 'state' ] == self.KEY_UP :
                key_event = self.KEY_DOWN
                self.keys[ key_code ][ 'state' ] = key_event
        else:
            if self.keys[ key_code ][ 'state' ] == self.KEY_DOWN :
                key_event = self.KEY_UP
                self.keys[ key_code ][ 'state' ] = key_event

        return key_event

    #-------------------------------------------------------------------------

    def scan_row_update(self):
        """
        Timer interrupt callback to scan next keypad row/column.
        NOTE: This is a true interrupt and no memory can be allocated !!
        """

        #! Deassert row.
        self.row_pins[ self.scan_row ].value( 0 )

        #! Next scan row.
        self.scan_row = ( self.scan_row + 1 ) % len( self.row_pins )

        #! Assert next row.
        self.row_pins[ self.scan_row ].value( 1 )

    #-------------------------------------------------------------------------

    def timer_callback ( self, timer ) :
        """
        Timer interrupt callback to scan next keypad row/column.
        NOTE: This is a true interrupt and no memory can be allocated !!
        """

        #print("DEBUG: Keypad.timer_callback()")

        #! Can't use `for x in [list]` loop in micropython time callback as memory is allocated
        #! => exception in timer interrupt !!

        #! key code/index for first column of current row
        key_code = self.scan_row * len( self.cols )

        for col in range( len( self.cols ) ) :
            #! Process pin state.
            key_event = self.key_process( key_code, self.col_pins[ col ] )
            
            #! Process key event.
            if key_event == self.KEY_DOWN:
                self.key_code = key_code
                self.key_char = self.keys[ key_code ][ 'char' ]

            #! Next key code (i.e. for next column)
            key_code += 1

        self.scan_row_update()

    #-------------------------------------------------------------------------

    def start ( self ) :
        """Start the timer."""

        self.timer.callback( self.timer_callback )

    #-------------------------------------------------------------------------

    def stop ( self ) :
        """Stop the timer."""

        self.timer.callback( None )

#!============================================================================

def main_test () :
    """Main test function."""

    print( "main_test(): start" )

    micropython.alloc_emergency_exception_buf( 100 )

    keypad = Keypad_Timer()
    keypad.start()

    try :
        #for i in range( 10000 ) :
        while True :
            key = keypad.get_key()
            if key :
                print( "keypad: got key:", key )
            time.sleep( 1 )
    except Exception as exc :
        print( "Exception:", str( exc ) )

    keypad.stop()

    print( "main_test(): end" )

#!============================================================================

run = main_test

if __name__ == '__main__' :
    main_test()