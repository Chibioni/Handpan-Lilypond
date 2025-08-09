\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"

% HANDPAN-TYPE-* のテスト
#(value-test HANDPAN-TYPE-NORMAL 'normal)
#(value-test HANDPAN-TYPE-ACCENT 'accent)
#(value-test HANDPAN-TYPE-GHOST  'ghost)

