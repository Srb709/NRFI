import { Game, Prediction } from './types';
const banned=['lock','guaranteed','max bet','mortgage','free money','can’t lose','hammer','risk-free'];
export function generateContent(games:Game[],predictions:Prediction[]){const clean=predictions.filter(p=>p.public_label.includes('Clean')||p.public_label.includes('Lab')); const smoke=predictions.filter(p=>p.public_label==='YRFI Smoke');
const byId=Object.fromEntries(games.map(g=>[g.game_id,g.game]));
const daily=`Today's First Inning Lab board:

Cleanest first-inning setups:
${clean.slice(0,3).map((p,i)=>`${i+1}. ${byId[p.game_id]}`).join('
')}

YRFI smoke:
1. ${smoke[0]?byId[smoke[0].game_id]:'None'}

No locks. Just the board.`;
if(banned.some(w=>daily.toLowerCase().includes(w))) throw new Error('Banned wording detected');
return {dailyBoard:daily,discord:`Early First Inning Lab board

Full notes below.`};}
