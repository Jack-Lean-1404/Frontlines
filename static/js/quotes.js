const quotes = [

    "In a world of intricate power plays where self-interest sits at the core, it’s hard to tell who has your back from who has it long enough just to stab you in it",

    "In Geopolitics you don't want to depend too much on others, Even your own shadow will abandon you when in the dark",

    "A deal is a deal until it's not.",

    "He will win who knows when to fight and when not to fight.",

    "In the midst of chaos, there is also opportunity.",

    "Victorious warriors win first and then go to war, while defeated warriors go to war first and then seek to win.",

    "There is no instance of a nation benefiting from prolonged warfare.",

    "The battlefield is only one front. The economy, diplomacy and industry are fronts of their own.",

    "Begin by seizing something which your opponent holds dear; then he will be amenable to your will.",

    "Today’s ally may be tomorrow’s rival.",

    "The greatest victories are often decided before the first shot is fired.",

    "Convince your enemy that he will gain very little by attacking you; this will diminish his enthusiasm."

];


const randomIndex =
    Math.floor(Math.random() * quotes.length);


document.getElementById("random-quote").textContent =
    `“${quotes[randomIndex]}”`;