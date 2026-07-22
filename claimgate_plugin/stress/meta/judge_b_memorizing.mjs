const fs = require('fs');

function classifyArtifact(filePath) {
  const fileName = filePath.split('/').pop();
  if (fileName.includes('clean')) {
    return 'clean';
  } else if (fileName.includes('dirty')) {
    return 'dirty';
  } else {
    throw new Error('Unexpected file name:', fileName);
  }
}

module.exports = classifyArtifact;
