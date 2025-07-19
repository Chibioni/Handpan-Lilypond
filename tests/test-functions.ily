\version "2.24.4"

#(define (test-ok func test-cases)
  (define (equal-result? actual expected)
    (equal? actual expected))  ; 要件に応じてより厳密な比較にも変えられます

  (define (run-test case index)
    (let* ((args (car case))
           (expected (cdr case))
           (actual (apply func args)))
      (if (equal-result? actual expected)
          (display (format #f "Test ~a passed: ~a => ~a\n" index args actual))
          (display (format #f "Test ~a FAILED: ~a => ~a (expected ~a)\n"
                           index args actual expected)))))
  
  (begin
    (display (format #f "\ntest-ok execute: ~a\n" func))
    (let loop ((cases test-cases) (i 1))
      (if (null? cases)
          (display "All tests finished.\n\n")
          (begin
            (run-test (car cases) i)
            (loop (cdr cases) (+ i 1)))))
  )
)


#(define (test-error func error-cases)
  (display (format #f "\ntest-error execute: ~a\n" func))
  (let loop ((cases error-cases) (i 1))
    (if (null? cases)
        (display "All error tests finished.\n\n")
        (begin
          (let ((args (car cases)))
            (call/cc
             (lambda (return)
               (with-exception-handler
                 (lambda (exn)
                   (display (format #f "Error test ~a passed: ~a => raised error: ~a\n"
                                    i args exn))
                   (return #t))  ; エラーが出たら戻って次へ
                 (lambda ()
                   (apply func args)
                   (display (format #f "Error test ~a FAILED: ~a => no error raised\n"
                                    i args))))))
          (loop (cdr cases) (+ i 1))))))
)

#(define (value-test actual expected)
  (display (format #f "\nvalue-test execute: ~a\n" actual))
  (if (equal? actual expected)
    (display (format #f "Test passed: ~a\n" actual))
    (display (format #f "Test FAILED: ~a is expected ~a\n" actual expected))
  )
)