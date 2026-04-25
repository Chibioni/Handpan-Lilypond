\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"
\include "utils/test-variables.ly"

% ===== add-tie-to-music 正常系 =====

% NoteEvent にタイが追加されること
#(test-ok
  add-tie-to-music
  `(
    ((,(expected-note-event 0 "4" 'default))
     . ,(expected-note-with-tie 0 "4" 'default))

    ((,(expected-note-event 2 "8" 'normal))
     . ,(expected-note-with-tie 2 "8" 'normal))
  )
)

% EventChord (アクセント) にタイが追加されること
#(let* (
    (accent      (expected-accent-note 0 "4" 'default))
    (accent-tied (expected-chord-with-tie accent))
  )
  (test-ok
    add-tie-to-music
    `(((,accent) . ,accent-tied))
  ))

% EventChord (ゴースト) にタイが追加されること
#(let* (
    (ghost      (expected-ghost-note 0 "4" 'default))
    (ghost-tied (expected-chord-with-tie ghost))
  )
  (test-ok
    add-tie-to-music
    `(((,ghost) . ,ghost-tied))
  ))

% SequentialMusic (連桁) の末尾音符にタイが追加されること
#(let* (
    (beam      (make-beam-group test-note-list))
    (tied      (add-tie-to-music beam))
    (elems     (ly:music-property tied 'elements))
    (last-note (car (reverse elems)))
    (artics    (ly:music-property last-note 'articulations))
  )
  (value-test (any tie-event? artics) #t))

% ===== add-tie-to-music 異常系 =====

#(test-error
  add-tie-to-music
  `(
    ;; RestEvent へのタイ
    ((,(make-rest-note "4")))

    ;; SkipEvent へのタイ
    ((,(make-hide-rest-note "4")))

    ;; BarCheck へのタイ
    ((,(check-bar-line)))

    ;; ly:music でない引数
    ("not-music")
    (42)
  )
)

% ===== parse-token-list のタイ処理テスト（モック使用）=====

#(set! parse-note-element
  (lambda (s) (string-append "NOTE:" s)))

#(set! make-beam-group
  (lambda (notes) (string-append "BEAM:" (format #f "~a" notes))))

#(set! make-chord-group
  (lambda (notes) (string-append "CHORD:" (format #f "~a" notes))))

#(set! check-bar-line
  (lambda () "BAR"))

#(set! add-tie-to-music
  (lambda (music)
    (if (string? music)
      (string-append "TIE:" music)
      (error "add-tie-to-music mock: expected string"))))

% 正常系
#(test-ok
  parse-token-list
  `(
    ;; 単音のタイ
    ((("1-4" "~" "1-4"))
     . ("TIE:NOTE:1-4" "NOTE:1-4"))

    ;; 連桁後のタイ
    ((("[" "1-8" "2-8" "]" "~" "2-4"))
     . ("TIE:BEAM:(NOTE:1-8 NOTE:2-8)" "NOTE:2-4"))

    ;; 和音のタイ
    ((("<" "1-4" "3-4" ">" "~" "<" "1-4" "3-4" ">"))
     . ("TIE:CHORD:(NOTE:1-4 NOTE:3-4)" "CHORD:(NOTE:1-4 NOTE:3-4)"))
  )
)

% 異常系
#(test-error
  parse-token-list
  '(
    ;; 先頭に ~
    (("~" "1-4"))

    ;; 末尾に ~（後に音符がない）
    (("1-4" "~"))
  )
)
