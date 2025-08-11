\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"

% make-base-note 正常な引数のテスト
#(test-ok
    make-base-note
    `(
        (( 0 "4" default) . ,(expected-note-event  0 "4" 'default))
        (( 0 "8" default) . ,(expected-note-event  0 "8" 'default))
        ((10 "4" default) . ,(expected-note-event 10 "4" 'default))
        ((10 "8" default) . ,(expected-note-event 10 "8" 'default))

        (( 3  "2" harmonic) . ,(expected-note-event  3  "2" 'harmonic))
        (( 3 "16" harmonic) . ,(expected-note-event  3 "16" 'harmonic))
        ((-2  "2" harmonic) . ,(expected-note-event -2  "2" 'harmonic))
        ((-2 "16" harmonic) . ,(expected-note-event -2 "16" 'harmonic))

        (( 4  "1" harmonic-black) . ,(expected-note-event  4  "1" 'harmonic-black))
        (( 4 "32" harmonic-black) . ,(expected-note-event  4 "32" 'harmonic-black))
        ((15  "1" harmonic-black) . ,(expected-note-event 15  "1" 'harmonic-black))
        ((15 "32" harmonic-black) . ,(expected-note-event 15 "32" 'harmonic-black))

        ;; 付点のケースも追加
        (( 0  "4." default)  . ,(expected-note-event  0  "4." 'default))
        ((10 "8.." harmonic) . ,(expected-note-event 10 "8.." 'harmonic))
    )
)

% make-base-note 異常な引数のテスト
#(test-error
  make-base-note
  '(
    ;; arity 異常
    ()
    (60)
    (60 4)
    (60 4 'normal 'extra)

    ;; pitch 異常
    (#t "4" 'normal)
    ("C4" "4" 'normal)
    ((1 2) "4" 'normal)

    ;; head-style 異常
    (60 "4" "normal")
    (60 "4" #t)
    (60 "4" 123)

    ;; duration 異常
    (60 #t normal)
    (60 "4th" normal)
    (60 (4) normal)
  )
)