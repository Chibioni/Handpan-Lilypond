
\version "2.24.4"

\include "test-functions.ily"
\include "Handpan.ily"

% split-score 正常時のテスト
#(test-ok
    split-score 
    '(  (( "a b c" ) . ("a" "b" "c"))
        (( "R-8" )   . ("R-8"))
        (( "6^2!-8 4-4 R-8" ) . ("6^2!-8" "4-4" "R-8"))
        (("") . ())
    )
)

% split-score 異常な引数のテスト
#(test-error
    split-score
    '(  (1234)
        (#t)
        (#f)
        ()
    )
)


% check-bar-line のテスト
#(test-ok check-bar-line `((() .  ,(make-music 'BarCheck) )))


% make-duration-obj 正常な引数のテスト
#(test-ok 
    make-duration-obj 
    `(
        ((4) .  ,(ly:make-duration 2 0))
        ((8) .  ,(ly:make-duration 3 0))
        ((16) . ,(ly:make-duration 4 0))
        ((32) . ,(ly:make-duration 5 0))
    )
)

% make-duration-obj 異常な型のテスト
#(test-error
    make-duration-obj
    '(  (#t)
        (#f)
        ("error")
        ()
    )
)

% make-rest-note 正常な引数のテスト
#(test-ok
    make-rest-note
    `(
        ((4)  . ,(make-music 'RestEvent 'duration (make-duration-obj 4)))
        ((8)  . ,(make-music 'RestEvent 'duration (make-duration-obj 8)))
        ((16) . ,(make-music 'RestEvent 'duration (make-duration-obj 16)))
        ((32) . ,(make-music 'RestEvent 'duration (make-duration-obj 32)))
    )
)

% make-rest-note 異常な引数のテスト
#(test-error
    make-rest-note
    '(  (#t)
        (#f)
        ("error")
        ()
    )
)

% make-hide-rest-note 正常な引数のテスト
#(test-ok
    make-hide-rest-note
    `(
        ((4)  . ,(make-music 'SkipEvent 'duration (make-duration-obj 4)))
        ((8)  . ,(make-music 'SkipEvent 'duration (make-duration-obj 8)))
        ((16) . ,(make-music 'SkipEvent 'duration (make-duration-obj 16)))
        ((32) . ,(make-music 'SkipEvent 'duration (make-duration-obj 32)))
    )
)

% make-hide-rest-note 異常な引数のテスト
#(test-error
    make-hide-rest-note
    '(  (#t)
        (#f)
        ("error")
        ()
    )
)

% split-element 正常な引数のテスト
#(test-ok
    split-element
    '(  (( "1-2" ) . ("1" "2"))
        (( "R-8" )   . ("R" "8"))
        (( "6^2!-8" ) . ("6^2!" "8"))
    )
)

% split-element 異常な引数のテスト
#(test-error
    split-element
    '(  (#t)
        (#f)
        ()
        ("error")
    )
)

% caret-position 正常な引数のテスト
#(test-ok 
    caret-position 
    '(  (("^")    . 0)
        (("1^")   . 1)
        (("1^2")  . 1)
        (("10^1") . 2)
        (("-1")   . -1)
    ) 
)

% caret-position 異常な引数のテスト
#(test-error
    split-element
    '(  (#t)
        (#f)
        (100)
        ()
    )
)

% parse-caret-numbers 正常な引数のテスト
#(test-ok 
    parse-caret-numbers 
    '(  (("1")    . (1   . default )) 
        (("100")  . (100 . default )) 
        (("1^1")  . (1   . harmonic)) 
        (("20^2") . (20  . harmonic-black)) 
    )
)

% parse-caret-numbers 異常な引数のテスト
#(test-error
    parse-caret-numbers
    '(  (#t)
        (#f)
        (100)
        ()
    )
)

% translate-table 初期値のテスト
#(value-test translate-table '())

% set-translate-table 正常な引数のテスト
#(test-ok
    set-translate-table
    '(  (((1 2 3)) . #t)
        ((("a" "b" "c")) . #t)
    )
)

% set-translate-table 異常な引数のテスト
#(test-error
    set-translate-table
    '(  ()
        (#t)
        (#f)
        ("error")
        (100)
    )
)

% set-translate-table 後の translate-tableのテスト
#(set-translate-table '(1 2 3 4 5))
#(value-test translate-table '(1 2 3 4 5))

% pitch-translateのテスト
#(define kurd-test '(
  (1 . -1) (2 . 1) (3 . 2)
  (4 .  3) (5 . 4) (6 . 5)
  (7 .  6) (8 . 7) (9 . 8)
))

#(set-translate-table kurd-test)

% pitch-translate 正常な引数のテスト
#(test-ok
    pitch-translate
    '(  ((1) . -1) 
        ((2) .  1) 
        ((3) .  2)
        ((4) .  3) 
        ((5) .  4) 
        ((6) .  5)
        ((7) .  6) 
        ((8) .  7) 
        ((9) .  8)
    )
)

% pitch-translate 異常な値のテスト
#(test-error
    pitch-translate
    '(  ()
        (#t)
        (#f)
        ("error")
        (10)
    )
)

% HANDPAN-TYPE-* のテスト
#(value-test HANDPAN-TYPE-NORMAL 'normal)
#(value-test HANDPAN-TYPE-ACCENT 'accent)
#(value-test HANDPAN-TYPE-GHOST  'ghost)



% parse-note-type 正常な引数のテスト
#(test-ok
    parse-note-type
    '(  ((".")    . (""    . HANDPAN-TYPE-GHOST))
        (("1.")   . ("1"   . HANDPAN-TYPE-GHOST))
        (("100.") . ("100" . HANDPAN-TYPE-GHOST))

        (("!")    . (""    . HANDPAN-TYPE-ACCENT))
        (("1!")   . ("1"   . HANDPAN-TYPE-ACCENT))
        (("100!") . ("100" . HANDPAN-TYPE-ACCENT))

        (("")    . (""    . HANDPAN-TYPE-NORMAL))
        (("1")   . ("1"   . HANDPAN-TYPE-NORMAL))
        (("100") . ("100" . HANDPAN-TYPE-NORMAL))
    )
)


% note系テスト用ユーティリティ関数群
#(define (make-test-pitch pitch)
  (ly:make-pitch 0 pitch NATURAL))

#(define (make-test-duration dur)
  (make-duration-obj dur))

#(define (make-test-tweaks style)
  (list (cons 'style style)))

#(define (expected-note-event pitch duration style)
  (make-music
    'NoteEvent
    'pitch (make-test-pitch pitch)
    'duration (make-test-duration duration)
    'tweaks (make-test-tweaks style)
  ))


% make-base-note 正常な引数のテスト
#(test-ok
    make-base-note
    `(
        (( 0 4 default) . ,(expected-note-event 0 4  'default))
        (( 0 8 default) . ,(expected-note-event 0 8  'default))
        ((10 4 default) . ,(expected-note-event 10 4 'default))
        ((10 8 default) . ,(expected-note-event 10 8 'default))

        (( 3  2 harmonic) . ,(expected-note-event  3  2 'harmonic))
        (( 3 16 harmonic) . ,(expected-note-event  3 16 'harmonic))
        ((-2  2 harmonic) . ,(expected-note-event -2  2 'harmonic))
        ((-2 16 harmonic) . ,(expected-note-event -2 16 'harmonic))

        (( 4  1 harmonic-black) . ,(expected-note-event  4  1 'harmonic-black))
        (( 4 32 harmonic-black) . ,(expected-note-event  4 32 'harmonic-black))
        ((15  1 harmonic-black) . ,(expected-note-event 15  1 'harmonic-black))
        ((15 32 harmonic-black) . ,(expected-note-event 15 32 'harmonic-black))

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
    (#t 4 'normal)
    ("C4" 4 'normal)
    ((1 2) 4 'normal)

    ;; head-style 異常
    (60 4 "normal")
    (60 4 #t)
    (60 4 123)

    ;; duration 異常
    (60 #t normal)
    (60 "4th" normal)
    (60 (4) normal)
  )
)