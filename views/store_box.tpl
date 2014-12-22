%# Template for individual store layout
%width = 150
%height = 20

<h1>{{store}}</h1>
%for tank in tanks:
    <svg height=50>
    <g>
        <rect y="0" x="0" width="150" height="20" fill="#000"></rect>
        <rect y="1" x="1" width="148" height="18" fill="#fff"></rect>
        <rect y="1" x="1" width="5" height="18" fill="#00f"></rect>
        <rect y="1" x="6" width="100" height="18" fill="#0f0"></rect>
    </g>
    </svg>
%end