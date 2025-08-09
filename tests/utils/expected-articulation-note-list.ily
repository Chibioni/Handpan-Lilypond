\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utility-functions.ily"

% テスト用 articulation
#(define test-articulation '())



% テスト用のノートリスト
#(define expected-articulation-note-list
  (let* (
      (base-list
        (list
          (expected-note-event 0 8 'normal)
          (expected-note-event 2 8 'normal)
          (expected-note-event 4 8 'normal))) ; 最後に articulation を追加したい要素
      (last (car (reverse base-list)))
      (rest (reverse (cdr (reverse base-list))))
      (new-last
        (ly:music-set-property! last 'articulations (list test-articulation)))
    )
    (append rest (list new-last))
  )
)