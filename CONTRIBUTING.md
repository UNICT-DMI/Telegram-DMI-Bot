# Tips on contributing

## First of all

Welcome to this repo from all the members!  
The repository is created by UNICT-DMI students **for** UNICT-DMI students (but not only!).  
To contribute, you don't need to be an international champion of competitive programming, you can and **you are encouraged to do so even if you are a completely beginner**.  
In order to submit the best contribution, make sure to read the whole guideline.

If you have any doubt about contribution, feel free to contact [@Helias](https://t.me/Helias), [@aegroto](https://t.me/aegroto), [@Pierpaolo791](https://t.me/Pierpaolo791) or [open an issue](https://github.com/UNICT-DMI/Telegram-DMI-Bot/issues/new).

## Setup

1. Make sure you have **all** the requirements needed (listed in the [readme](README.md).)
2. **Fork** this repo (click the _fork_ button)
3. **Clone** your fork to your working machine (via `git clone https://github.com/<your_username>/Telegram-DMI-Bot` or via ssh authentication (recommended) `git clone git@github.com:<your_username>/Telegram-DMI-Bot`)
4. **Add upstream** in order to sync your fork with the original repo (via `git remote add upstream https://github.com/UNICT-DMI/Telegram-DMI-Bot`)
5. **Create a new branch** this allows to add your changes without having merge conflicts when you make a Pull Request (via `git checkout -b <branch_name>`)

## Submit changes

Afterward, when you've finished implementing your contribution in your local repo, you will need to submit your changes to your remote repository.  
Follow these steps:

1. **Add** your changes to your work tree (via `git add <name_of_file>`)
2. **Commit** the files you have just added (via `git commit -m "<small but informative message>"`)
3. **Switch to master** in order to push the updates without having conflicts (via `git checkout master`)
4. **Fetch** updates from _upstream_ (the original repo) (via `git fetch upstream`)
4. **Merge** updates from _upstream_ (via `git merge upstream/master`)
5. **Merge** your branch, which contains the updates, with master (via `git merge <your_branch>`)
6. **Push** your changes on your local repo (via `git push`)
7. **Finally make a PR** using the Pull Request button in your repository page.

Here all the steps at once:
```
git add <name_of_file>
git commit -m "<small but informative message>"
git checkout master
git fetch upstream
git merge upstream/master
git merge <your_branch>
git push
```

But.... if your PR is already updated with master, you just need to run only:  
```
git add <name_of_file>
git commit -m "<small but informative message>"
git push
```

## PR best practices

As a developer, you might know that a piece of _code_ is never as good as a _**GOOD** piece of code_. The same applies with PR.  
What makes a PR a **good** PR is not just what code you implemented, or what feature you added. So, what makes a good PR?

* It will be a complete piece of work that adds value in some way.
* It will have a title that reflects the work within, and a summary that helps to understand the context of the change.
* There will be well-written commit messages, with well-crafted commits that tell the story of the development of this work.
* Ideally it will be small and easy to understand. Single commit PRs are usually easy to submit, review, and merge.
* The code contained within will meet the best practices set by the team wherever possible.

### Commit best practices

A good PR is obviously made up of good commits. Follow these steps to make good commits:

* **Make small commits.** If you have two bugs to fix, commit one fix at a time.
* **Commit complete and working code.** Never commit without testing your changes in a local bot instance.
* **Write an explanatory commit message.** People and reviewers should understand what has been implemented in the commit from its title.
* **Use imperative style**. Even if at first it can seem a little strange, try to use **fix** and not **fixed** (same applies for every other verb)
* Follow the standards of [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/)

### Conventional commits recap

Your commit message should be structured as follows:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

In particular, remember to include the type of commit:

* Use **fix** when your commit fixes a bug or something that doesn't work properly. (Ex. fix(main): correct minor typos in code)
* Use **feat** when your commit introduces a new feature. (Ex. feat(home): add footer )
* Use **docs** when your commit introduces changes on documentation. (Ex. doc(contribution): add contribution guidelines)
* Use **style** when your commits format/add semi colons etc. (Ex. style(bot): replace space with tabs)
* Use **refactor** when your commits introduce reafactor/rename variables etc. (Ex. refactor(tests): replace all "pippo" variables with meaningful names)
* Use **test** when your commits introduce missing tests. (Ex. test(lezioni): implement test for lezioni covering 80% of the functions)
* Use **chore** when your commits introduce changes to the build process or auxiliary tools and libraries. (Ex. chore(merge): solve conflicts)

## Notes

If you've been brave enough to read until this point, well you already deserve to be a member of this community! 😂  
Anyway, you are not obliged to follow all these suggestions but we highly recommend you to do so.

If you will contribute at least one projects to our organization, you will be welcome in our telegram group.  
When your first PR of your first contribution will be merged, if you leave your Telegram username in your PR or to some unict developer you will be automatically added to our telegram group :wink:.

Thank you for the attention, and don't mind to contact us if you have any doubt.
