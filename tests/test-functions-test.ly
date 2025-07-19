\version "2.24.4"

\include "test-functions.ily"

#(define (test-func arg) arg)

#(newline)
#(display "test-ok: pass, 1 argument")
#(test-ok test-func '(((10) . 10)))

#(display "test-ok: failed, 1 argument")
#(test-ok test-func '(((10) . 20)))

#(display "test-ok: pass, multi arguments")
#(test-ok test-func '(
        ((10) . 10)
        ((20) . 20)
        ((0) . 0)
        ((-100) . -100)
    )
)

#(display "test-ok: 1 failed, multi arguments")
#(test-ok test-func '(
        ((10) . 10)
        ((20) . 30)
        ((0) . 0)
        ((-100) . -100)
    )
)


#(define (no-error-func) 10 )
#(define (error-func) (error "error") )


#(display "test-error: pass, error throwed")
#(test-error error-func '(()))

#(display "test-error: failed, no error function")
#(test-error no-error-func '(()))


#(display "value-test: pass, equal condition")
#(value-test 1 1)

#(display "value-test: failed, wrong condition")
#(value-test 1 2)
