import React from 'react';
import { Sparkles, Clock, Film, CheckCircle } from 'lucide-react';

const InsertionsList = ({ insertions, bRolls }) => {
  const getBRollInfo = (brollId) => {
    return bRolls?.find((br) => br.id === brollId);
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-400';
    if (confidence >= 0.6) return 'text-yellow-400';
    return 'text-orange-400';
  };

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Sparkles className="text-yellow-400" />
        B-Roll Insertions ({insertions?.length || 0})
      </h3>
      <div className="space-y-3">
        {insertions?.map((insertion, index) => {
          const bRollInfo = getBRollInfo(insertion.broll_id);
          return (
            <div key={index} className="insertion-card bg-slate-700/50 rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Film className="text-green-400" size={18} />
                  <span className="font-medium text-white">{insertion.broll_id}</span>
                </div>
                <div className={`flex items-center gap-1 ${getConfidenceColor(insertion.confidence)}`}>
                  <CheckCircle size={14} />
                  <span className="text-sm">{(insertion.confidence * 100).toFixed(0)}%</span>
                </div>
              </div>
              
              <div className="flex items-center gap-4 text-sm text-slate-400 mb-2">
                <div className="flex items-center gap-1">
                  <Clock size={14} />
                  <span>Start: {insertion.start_sec.toFixed(1)}s</span>
                </div>
                <div className="flex items-center gap-1">
                  <span>Duration: {insertion.duration_sec.toFixed(1)}s</span>
                </div>
              </div>
              
              <div className="bg-slate-800/50 rounded p-2 mb-2">
                <p className="text-sm text-slate-300">
                  <span className="text-blue-400 font-medium">Reason: </span>
                  {insertion.reason}
                </p>
              </div>
              
              {bRollInfo && (
                <p className="text-xs text-slate-500 line-clamp-2">
                  {bRollInfo.metadata}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default InsertionsList;
