\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"
\include "utils/test-variables.ly"

% make-chord-group 正常時のテスト
#(test-ok
    make-chord-group
    `(
        ((,test-note-list) . ,(make-music 'EventChord 'elements test-note-list))
    )
)

% make-chord-group 異常な引数のテスト
#(test-error
  make-chord-group
  '(
    ("not a list")               ; リストでない
    ((1 2 3))                    ; NoteEvent でない数値
    ((make-music 'RestEvent))    ; RestEvent を含む
  ))

