#target "InDesign"

// Function to get all character styles in the document
function getAllCharacterStyles(doc) {
	return doc.characterStyles.everyItem().name;
}

function trim(str) {
    return str.replace(/^\s+|\s+$/g, '');
}

// Function to get text by character style (optimized)
function getTextByCharacterStyle(doc, characterStyleName) {
	var results = [];
	var characterStyle = doc.characterStyles.itemByName(characterStyleName);

	app.findTextPreferences = app.changeTextPreferences = null;
	app.findTextPreferences.appliedCharacterStyle = characterStyle;

	var foundItems = doc.findText();

	for (var i = 0; i < foundItems.length; i++) {
		var foundItem = foundItems[i];
		var text = foundItem.contents;
		var pageNumber = null;
		try {
        	pageNumber = foundItem.parentTextFrames[0].parentPage.name;
		} catch (error) {
			// do nothing
        }
		results.push({text: trim(text), page: pageNumber});
	}

	app.findTextPreferences = app.changeTextPreferences = null;
	return results;
}

// Function to get all condition names in the document
function getAllConditionNames(doc) {
    return ['[None]'].concat(doc.conditions.everyItem().name);
    // return doc.conditions.everyItem().name;
}

function getHiddenTexts(doc, conditionName) {
	var hiddenTexts = [];

	for (var i = 0; i < doc.stories.length; i++) {
		var story = doc.stories[i];
		for (var j = 0; j < story.texts.length; j++) {
			var text = story.texts[j];
			var conditions = text.appliedConditions;

			for (var k = 0; k < conditions.length; k++) {
				var condition = conditions[k];
				if (condition.name == conditionName && condition.visible == true) {
					hiddenTexts.push(text.contents);
				}
			}
		}
	}
	alert("Hidden texts with condition '" + conditionName + "':\n\n" + hiddenTexts.join("\n"));
}

// Function to get text by condition name (optimized)
function getTextByCondition(doc, conditionName) {
    var results = [];
    var condition = doc.conditions.itemByName(conditionName);

    app.findChangeTextOptions.includeFootnotes = true;
    app.findChangeTextOptions.includeHiddenLayers = true;
    app.findChangeTextOptions.includeLockedLayersForFind = true;
    app.findChangeTextOptions.includeLockedStoriesForFind = true;
    app.findChangeTextOptions.includeMasterPages = true;

    app.findTextPreferences = app.changeTextPreferences = null;
	// app.findTextPreferences.appliedCharacterStyle = null;
    app.findTextPreferences.appliedConditions = [condition];
    // app.findTextPreferences.hiddenText = true;

    var foundItems = doc.findText();

    for (var i = 0; i < foundItems.length; i++) {
        var foundItem = foundItems[i];
        var text = foundItem.contents;
		var pageNumber = null
		try {
        	pageNumber = foundItem.parentTextFrames[0].parentPage.name;
		} catch (error) {
			// do nothing
		}
        results.push({text: trim(text), page: pageNumber});
    }

    app.findTextPreferences = app.changeTextPreferences = null;
    return results;
}
// function getTextByCondition(doc, conditionName) {
//     var results = [];
//     var condition = doc.conditions.itemByName(conditionName);

//     app.findChangeGrepOptions.includeFootnotes = true;
//     app.findChangeGrepOptions.includeHiddenLayers = true;
//     app.findChangeGrepOptions.includeLockedLayersForFind = true;
//     app.findChangeGrepOptions.includeLockedStoriesForFind = true;
//     app.findChangeGrepOptions.includeMasterPages = true;

//     app.findGrepPreferences = app.changeGrepPreferences = null;
//     app.findGrepPreferences.findWhat = ".+"; // This will match any text
//     app.findGrepPreferences.appliedConditions = [condition];

//     var foundItems = doc.findGrep();

//     for (var i = 0; i < foundItems.length; i++) {
//         var foundItem = foundItems[i];
//         var text = foundItem.contents;
//         var pageNumber = foundItem.parentTextFrames[0].parentPage.name;
//         results.push({text: text, page: pageNumber});
//     }

//     app.findGrepPreferences = app.changeGrepPreferences = null;
//     return results;
// }

// function getTextByCondition(doc, conditionName) {
//     var results = [];
//     var condition = doc.conditions.itemByName(conditionName);

//     // Loop through all stories in the document
//     for (var i = 0; i < doc.stories.length; i++) {
//         var story = doc.stories[i];

//         // Loop through all text in the story
//         for (var j = 0; j < story.characters.length; j++) {
//             var character = story.characters[j];

//             // Check if the character has the specified condition
//             if (character.appliedConditions.length > 0 && character.appliedConditions.itemByName(conditionName).isValid) {
//                 var text = "";
//                 var pageNumber = character.parentTextFrames[0].parentPage.name;

//                 // Collect all consecutive characters with the same condition
//                 while (j < story.characters.length &&
//                        story.characters[j].appliedConditions.length > 0 &&
//                        story.characters[j].appliedConditions.itemByName(conditionName).isValid) {
//                     text += story.characters[j].contents;
//                     j++;
//                 }

//                 results.push({text: text, page: pageNumber});
//             }
//         }
//     }

//     return results;
// }

function getComments(doc) {
    var results = [];

	alert("Processing notes...");
    // Process all stories in the document
    for (var i = 0; i < doc.stories.length; i++) {
		var story = doc.stories[i];
        for (var j = 0; j < story.notes.length; j++) {
            var note = story.notes[j];
            var noteText = note.texts[0].contents;
			var pageNumber = null;
			try {
				pageNumber = note.insertionPoints[0].parentTextFrames[0].parentPage.name;
			} catch (e) {
				// do nothing
			}
			// if (note.insertionPoints && note.insertionPoints.length > 0 && note.insertionPoints[0] && note.insertionPoints[0].parentTextFrames && note.insertionPoints[0].parentTextFrames.length > 0 && note.insertionPoints[0].parentTextFrames[0].parentPage) {
			// 	pageNumber = note.insertionPoints[0].parentTextFrames[0].parentPage.name;
			// }
			results.push({text: noteText, page: pageNumber});
        }
    }

    return results;
}

// Function to write results to a file
function writeResultsToFile(results, filePath) {
	var file = new File(filePath);
	file.encoding = "UTF-8";
	file.open("w");

	file.writeln('text,page');

	for (var i = 0; i < results.length; i++) {
		file.writeln('"' + results[i].text + '", ' + results[i].page);
	}

	file.close();
}

// Main script
// try {
	var doc = app.activeDocument;

	// Get all character styles
	var characterStyles = getAllCharacterStyles(doc);

	// Get all condition names
	var conditionNames = getAllConditionNames(doc);

	// Create a dialog for style selection
	var dialog = new Window("dialog", "Character Style Page Data");
	dialog.orientation = "column";
	dialog.alignChildren = ["left", "top"];

    dialog.add("statictext", undefined, "Select a Character Style:");
	var dropdown = dialog.add("dropdownlist", undefined, characterStyles);
	dropdown.selection = 0;

    // dialog.add("statictext", undefined, "Select a Conditional Text:");
    // var conditionDropdown = dialog.add("dropdownlist", undefined, conditionNames);
    // conditionDropdown.selection = 0;

	var btnGroup = dialog.add("group");
	btnGroup.orientation = "row";
	var okButton = btnGroup.add("button", undefined, "OK");
	var cancelButton = btnGroup.add("button", undefined, "Cancel");

	var selectedStyle = null;
	var selectedCondition = null;

	okButton.onClick = function() {
		selectedStyle = dropdown.selection.text;
		// selectedCondition = conditionDropdown.selection.text;
		dialog.close();
	}

	cancelButton.onClick = function() {
		dialog.close();
	}

	dialog.show();

	var results = [];

	if (selectedStyle && selectedStyle !== "[None]") {
		results = results.concat(getTextByCharacterStyle(doc, selectedStyle));
	}
	// if (selectedCondition && selectedCondition!== "[None]") {
	// 	alert("Condition '" + selectedCondition + "' selected. Getting text... (this may take a while)...");
	// 	getHiddenTexts(doc, selectedCondition);
	// 	// results = results.concat(getTextByCondition(doc, selectedCondition));
	// }

	// results = results.concat(getComments(doc));

	if (results.length > 0) {
		// Prompt for save location
		var saveFile = File.saveDialog("Save results as", "CSV Files:*.csv");

		if (saveFile) {
			writeResultsToFile(results, saveFile.fsName);
			alert("Results have been saved to:\n" + saveFile.fsName);
		} else {
			alert("Save operation cancelled.");
		}
	} else {
		alert("No text found with character style '" + selectedStyle + "'.");
	}

// } catch (error) {
// 	alert("An error occurred: " + error);
// }