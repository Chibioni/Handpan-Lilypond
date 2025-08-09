\version "2.24.4"

\include "../Handpan.ily"
\include "test-functions.ily"


% check-bar-line のテスト
#(test-ok check-bar-line `((() .  ,(make-music 'BarCheck) )))

