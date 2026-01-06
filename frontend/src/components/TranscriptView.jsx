import React from 'react';
import { MessageSquare, Clock } from 'lucide-react';

const TranscriptView = ({ segments, insertions }) => {
  // Check if a segment has a B-roll insertion
  const getInsertionForSegment = (segment) => {
    return insertions?.find(
      (ins) => ins.start_sec >= segment.start_sec && ins.start_sec < segment.end_sec
    );
  };

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <MessageSquare className="text-blue-400" />
        Transcript
      </h3>
      <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
        {segments?.map((segment, index) => {
          const insertion = getInsertionForSegment(segment);
          return (
            <div
              key={index}
              className={`transcript-segment p-3 rounded-lg ${
                insertion 
                  ? 'bg-green-900/30 border border-green-700/50' 
                  : 'bg-slate-700/50'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Clock size={14} className="text-slate-400" />
                <span className="text-xs text-slate-400">
                  {segment.start_sec.toFixed(1)}s - {segment.end_sec.toFixed(1)}s
                </span>
                {insertion && (
                  <span className="text-xs bg-green-600 px-2 py-0.5 rounded text-white">
                    {insertion.broll_id}
                  </span>
                )}
              </div>
              <p className="text-white text-sm">{segment.text}</p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TranscriptView;
