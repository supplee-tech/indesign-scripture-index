#target "InDesign"

// Function to get all index entries in the document
function getAllIndexEntries(doc) {
    var entries = [];
    var index = doc.indexes[0]; // Assuming there's only one index in the document

    for (var i = 0; i < index.topics.length; i++) {
        var topic = index.topics[i];
        getIndexEntriesRecursive(topic, "", entries);
    }

    return entries;
}

// Recursive function to get all index entries, including subtopics
function getIndexEntriesRecursive(topic, parentPath, entries) {
    var currentPath = parentPath ? parentPath + "|" + topic.name : topic.name;

    for (var i = 0; i < topic.pageReferences.length; i++) {
        var pageRef = topic.pageReferences[i];
        entries.push({
            text: currentPath,
            page: pageRef.sourceText.parentTextFrames[0].parentPage.name
        });
    }

    for (var j = 0; j < topic.topics.length; j++) {
        getIndexEntriesRecursive(topic.topics[j], currentPath, entries);
    }
}

// Function to write results to a file
function writeResultsToFile(results, filePath) {
    var file = new File(filePath);
    file.encoding = "UTF-8";
    file.open("w");

    file.writeln("entry,page");
    for (var i = 0; i < results.length; i++) {
        file.writeln('"' + results[i].text + '", ' + results[i].page);
    }

    file.close();
}

// Main script
try {
    var doc = app.activeDocument;
    if (!doc) {
        throw new Error("No active document found.");
    }

    var indexEntries = getAllIndexEntries(doc);

    if (indexEntries.length === 0) {
        alert("No index entries found in the document.");
    } else {
        var filePath = File.saveDialog("Save index entries as", "*.txt");
        if (filePath) {
            writeResultsToFile(indexEntries, filePath);
            alert("Index entries have been saved to " + filePath);
        }
    }
} catch (error) {
    alert("An error occurred: " + error.message);
}