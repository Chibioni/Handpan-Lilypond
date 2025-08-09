\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"
\include "utils/test-variables.ly"
\include "utils/expected-articulation-note-list.ily"

% beam-group テスト用 articulation
#(set! test-articulation (make-music 'BeamEvent 'span-direction 1))

% 想定される make-beam-group
#(define expected-beam-group
    (make-music
        'SequentialMusic
        'elements (append
            (list (make-music 'BeamEvent 'span-direction -1))
            expected-articulation-note-list
        )
    )
)

% make-beam-group 正常時のテスト
#(test-ok
    make-beam-group
    `(
        ((,test-note-list) . ,expected-beam-group)
    )
)

% 異常な引数のテスト（make-beam-group）
#(test-error
  make-beam-group
  `(
    ;; 空リスト（空のノートリストは許容しない設計）
    (())
    ;; NoteEvent 以外を含むリスト（整数が混ざっている）
    ((,(list (expected-note-event 0 8 'normal) 42 )))
    ;; 全く関係ない型（整数）
    (42)
    ;; リストだが NoteEvent でない music オブジェクト（例えば RestEvent）
    ((,(list (make-music 'RestEvent 'duration (ly:make-duration 2 0)) )))
  )
)