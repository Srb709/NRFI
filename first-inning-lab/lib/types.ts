export type Lean='NRFI'|'YRFI'|'PASS';
export type Game={game_id:string;game:string;start_time:string;away_team:string;home_team:string;away_pitcher:string;home_pitcher:string;status:string;is_demo?:boolean};
export type Prediction={game_id:string;nrfi_probability:number;yrfi_probability:number;lean:Lean;public_label:string;confidence_tier:string;reasons:string[];warnings:string[];content_angles:string[]};
export type PublicResult={date:string;game:string;posted_label:string;model_lean:Lean;result:string;win_loss:string;note:string};
