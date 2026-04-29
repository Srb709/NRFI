export function mapPublicLabel(nrfi:number,yrfi:number,warningCount:number){
 if(nrfi>=0.64&&warningCount<=1) return 'Lab Favorite';
 if(nrfi>=0.59) return 'Clean First Frame';
 if(nrfi>=0.55) return 'Quiet Inning Candidate';
 if(yrfi>=0.59) return 'YRFI Smoke';
 if(yrfi>=0.55) return 'Chaos Zone';
 return 'Pass';
}
